"""Content summarization classes for news articles and YouTube videos"""

import asyncio
import logging
import re
from urllib.parse import parse_qs, urlparse

from newspaper import Article
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import pytube
import aiohttp
import json

from constants import (
    ARTICLE_MAX_TEXT_LENGTH, TRANSCRIPT_MAX_LENGTH,
    NEWS_SITE_PATTERNS, YOUTUBE_URL_PATTERNS
)
from security import InputValidator

logger = logging.getLogger(__name__)


class NewsSummarizer:
    """Handles news article summarization using Ollama AI"""

    def __init__(self, ollama_client):
        self.ollama = ollama_client
        # Common news site patterns
        self.news_regex = re.compile('|'.join(NEWS_SITE_PATTERNS), re.IGNORECASE)
        self.validator = InputValidator()

    def extract_urls(self, text: str) -> list[str]:
        """Extract URLs from text and filter for news sites"""
        # URL pattern
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        urls = url_pattern.findall(text)

        # Filter for news sites
        news_urls = []
        for url in urls:
            if self.news_regex.search(url):
                news_urls.append(url)

        return news_urls

    async def extract_article_content(self, url: str) -> dict:
        """Extract article content using newspaper3k"""
        try:
            # SECURITY: Add timeout protection for external requests
            import asyncio
            article = Article(url)

            # Use asyncio.wait_for to add timeout
            await asyncio.wait_for(
                asyncio.to_thread(article.download),
                timeout=30.0  # 30 second timeout
            )
            await asyncio.wait_for(
                asyncio.to_thread(article.parse),
                timeout=15.0  # 15 second timeout for parsing
            )

            if not article.title or not article.text:
                return {"success": False, "error": "Could not extract article content"}

            return {
                "success": True,
                "title": article.title,
                "text": article.text,
                "url": url,
                "authors": article.authors,
                "publish_date": article.publish_date,
                "summary": article.summary if hasattr(article, 'summary') else None
            }
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Error extracting article from {url}: {error_type}")

            # Check if this is a paywall/access issue - try multiple archive fallbacks
            is_access_blocked = (
                "403" in str(e) or
                "forbidden" in str(e).lower() or
                "paywall" in str(e).lower() or
                "subscription" in str(e).lower() or
                "blocked" in str(e).lower()
            )

            if is_access_blocked:
                logger.info(f"Access blocked, trying archive fallbacks for {url}")

                # Try multiple archive services in order
                archive_services = [
                    ("archive.is", self._extract_from_archive_is),
                    ("web.archive.org", self._extract_from_wayback_machine),
                    ("archive.today", self._extract_from_archive_today),
                ]

                for service_name, extractor_func in archive_services:
                    logger.info(f"Trying {service_name} fallback for {url}")
                    try:
                        archive_result = await extractor_func(url)
                        if archive_result["success"]:
                            logger.info(f"Successfully extracted article from {service_name} for {url}")
                            return archive_result
                        else:
                            logger.warning(f"{service_name} fallback failed for {url}")
                    except Exception as archive_e:
                        logger.error(f"{service_name} fallback failed for {url}: {type(archive_e).__name__}")
                        continue

                # If all archives failed, try alternative extraction methods
                logger.info(f"Trying alternative extraction methods for {url}")
                try:
                    alt_result = await self._extract_with_alternative_methods(url)
                    if alt_result["success"]:
                        logger.info(f"Successfully extracted article using alternative methods for {url}")
                        return alt_result
                    else:
                        logger.warning(f"Alternative extraction methods also failed for {url}")
                except Exception as alt_e:
                    logger.error(f"Alternative extraction failed for {url}: {type(alt_e).__name__}")

                logger.warning(f"All extraction methods failed for {url}")

            # Provide more user-friendly error messages
            if "timeout" in str(e).lower() or error_type == "TimeoutError":
                error_msg = "Article took too long to load"
            elif is_access_blocked:
                error_msg = "Article access blocked (possibly paywall or region restriction)"
            elif "404" in str(e) or "not found" in str(e).lower():
                error_msg = "Article not found"
            elif "connection" in str(e).lower():
                error_msg = "Network connection error"
            else:
                error_msg = f"Could not extract article content ({error_type})"

            return {"success": False, "error": error_msg}

    async def _extract_from_archive_is(self, url: str) -> dict:
        """Try to extract article from archive.is as fallback for blocked content"""
        try:
            # Create archive.is URL
            archive_url = f"https://archive.is/{url}"

            # Try to extract from archived version
            article = Article(archive_url)

            # Use asyncio.wait_for to add timeout
            await asyncio.wait_for(
                asyncio.to_thread(article.download),
                timeout=45.0  # Longer timeout for archive
            )
            await asyncio.wait_for(
                asyncio.to_thread(article.parse),
                timeout=20.0  # Longer timeout for parsing
            )

            if not article.title or not article.text:
                return {"success": False, "error": "Could not extract archived article content"}

            return {
                "success": True,
                "title": f"[Archived] {article.title}",
                "text": article.text,
                "url": archive_url,  # Use archive URL
                "authors": article.authors,
                "publish_date": article.publish_date,
                "summary": article.summary if hasattr(article, 'summary') else None,
                "source": "archive.is"
            }

        except Exception as e:
            logger.error(f"Error extracting from archive.is for {url}: {type(e).__name__}")
            return {"success": False, "error": f"Archive extraction failed: {type(e).__name__}"}

    async def _extract_from_wayback_machine(self, url: str) -> dict:
        """Try to extract article from Internet Archive Wayback Machine"""
        try:
            # First get the latest available snapshot
            availability_url = f"https://archive.org/wayback/available?url={url}"

            async with aiohttp.ClientSession() as session:
                async with session.get(availability_url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        snapshots = data.get("archived_snapshots", {})
                        closest = snapshots.get("closest")

                        if closest and closest.get("available"):
                            archive_url = closest["url"]
                        else:
                            # Fallback: try a common archived URL pattern
                            archive_url = f"https://web.archive.org/web/20240000000000*/{url}"
                    else:
                        return {"success": False, "error": "Could not find archived version"}

            # Extract from the archived URL
            article = Article(archive_url)

            await asyncio.wait_for(
                asyncio.to_thread(article.download),
                timeout=45.0
            )
            await asyncio.wait_for(
                asyncio.to_thread(article.parse),
                timeout=20.0
            )

            if not article.title or not article.text:
                return {"success": False, "error": "Could not extract archived article content"}

            return {
                "success": True,
                "title": f"[Archived] {article.title}",
                "text": article.text,
                "url": archive_url,
                "authors": article.authors,
                "publish_date": article.publish_date,
                "summary": article.summary if hasattr(article, 'summary') else None,
                "source": "wayback machine"
            }

        except Exception as e:
            logger.error(f"Error extracting from Wayback Machine for {url}: {type(e).__name__}")
            return {"success": False, "error": f"Wayback Machine extraction failed: {type(e).__name__}"}

    async def _extract_from_archive_today(self, url: str) -> dict:
        """Try to extract article from archive.today"""
        try:
            # Create archive.today URL
            archive_url = f"https://archive.today/{url}"

            article = Article(archive_url)

            await asyncio.wait_for(
                asyncio.to_thread(article.download),
                timeout=45.0
            )
            await asyncio.wait_for(
                asyncio.to_thread(article.parse),
                timeout=20.0
            )

            if not article.title or not article.text:
                return {"success": False, "error": "Could not extract archived article content"}

            return {
                "success": True,
                "title": f"[Archived] {article.title}",
                "text": article.text,
                "url": archive_url,
                "authors": article.authors,
                "publish_date": article.publish_date,
                "summary": article.summary if hasattr(article, 'summary') else None,
                "source": "archive.today"
            }

        except Exception as e:
            logger.error(f"Error extracting from archive.today for {url}: {type(e).__name__}")
            return {"success": False, "error": f"Archive.today extraction failed: {type(e).__name__}"}

    async def _extract_with_alternative_methods(self, url: str) -> dict:
        """Try alternative extraction methods when archives fail"""
        try:
            # Method 1: Try with different User-Agent
            import aiohttp
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        html_content = await response.text()

                        # Try to extract with newspaper but with raw HTML
                        article = Article(url)
                        article.set_html(html_content)

                        await asyncio.wait_for(
                            asyncio.to_thread(article.parse),
                            timeout=15.0
                        )

                        if article.title and article.text:
                            return {
                                "success": True,
                                "title": article.title,
                                "text": article.text,
                                "url": url,
                                "authors": article.authors,
                                "publish_date": article.publish_date,
                                "summary": article.summary if hasattr(article, 'summary') else None,
                                "source": "direct with headers"
                            }

            # Method 2: Try with readability-based extraction
            try:
                from readability import Document
                import requests

                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == 200:
                    doc = Document(response.text)
                    title = doc.title()
                    content = doc.summary()

                    if title and content:
                        # Clean up HTML tags from content
                        import re
                        clean_content = re.sub(r'<[^>]+>', '', content)
                        clean_content = re.sub(r'\s+', ' ', clean_content).strip()

                        if len(clean_content) > 200:  # Minimum content length
                            return {
                                "success": True,
                                "title": title,
                                "text": clean_content,
                                "url": url,
                                "authors": [],
                                "publish_date": None,
                                "summary": None,
                                "source": "readability extraction"
                            }
            except ImportError:
                logger.debug("Readability library not available, skipping alternative extraction")
            except Exception as readability_e:
                logger.debug(f"Readability extraction failed: {type(readability_e).__name__}")

        except Exception as e:
            logger.error(f"Alternative extraction methods failed for {url}: {type(e).__name__}")

        return {"success": False, "error": "All extraction methods failed"}

    async def summarize_with_ai(self, article_data: dict) -> str:
        """Use AI to summarize the article"""
        if not article_data["success"]:
            error_msg = article_data.get("error", "Could not extract article content")
            return f"❌ {error_msg}"

        title = article_data["title"]
        text = article_data["text"]

        # Truncate text if too long
        if len(text) > ARTICLE_MAX_TEXT_LENGTH:
            text = text[:ARTICLE_MAX_TEXT_LENGTH] + "..."

        prompt = f"""Please provide a concise summary of the following news article:

Title: {title}

Content:
{text}

Please provide:
1. A brief 2-3 sentence summary
2. Key points (bullet format)
3. Important context if relevant

Keep it informative but concise."""

        try:
            summary = await self.ollama.generate(prompt)
            return summary
        except Exception as e:
            logger.error(f"Error generating summary: {type(e).__name__}")
            return "❌ Failed to generate article summary."

    async def process_article(self, url: str) -> str:
        """Process a single article and return summary"""
        # Validate URL
        valid, validation_msg = self.validator.validate_url(url)
        if not valid:
            return f"❌ {validation_msg}"

        # Extract content
        article_data = await self.extract_article_content(url)

        if not article_data["success"]:
            return f"❌ Failed to extract article: {article_data['error']}"

        # Generate AI summary
        summary = await self.summarize_with_ai(article_data)

        # Format response
        title = article_data["title"]
        authors = ", ".join(article_data["authors"]) if article_data["authors"] else "Unknown"
        publish_date = article_data["publish_date"].strftime("%Y-%m-%d") if article_data["publish_date"] else "Unknown"

        # Check if this came from archive
        source_indicator = ""
        source_url = url
        source_type = article_data.get("source", "original")

        if source_type == "archive.is":
            source_indicator = "📚 *Archived Content* (accessed via archive.is)\n"
            source_url = article_data.get("url", url)
        elif source_type == "wayback machine":
            source_indicator = "📚 *Archived Content* (accessed via Internet Archive)\n"
            source_url = article_data.get("url", url)
        elif source_type == "archive.today":
            source_indicator = "📚 *Archived Content* (accessed via archive.today)\n"
            source_url = article_data.get("url", url)
        elif source_type == "direct with headers":
            source_indicator = "📄 *Content extracted* (using alternative headers)\n"
        elif source_type == "readability extraction":
            source_indicator = "📄 *Content extracted* (using readability parser)\n"

        response = f"📰 *{title}*\n\n"
        if source_indicator:
            response += f"{source_indicator}\n"
        response += f"👤 *Authors:* {authors}\n"
        response += f"📅 *Published:* {publish_date}\n"
        response += f"🔗 *Source:* [Read More]({source_url})\n\n"
        response += "📋 *Summary:*\n"
        response += summary

        return response


class YouTubeSummarizer:
    """Handles YouTube video summarization using transcripts and AI"""

    def __init__(self, ollama_client):
        self.ollama = ollama_client
        # YouTube URL patterns
        self.youtube_regex = re.compile('|'.join(YOUTUBE_URL_PATTERNS), re.IGNORECASE)
        self.validator = InputValidator()

    def extract_video_urls(self, text: str) -> list[str]:
        """Extract YouTube URLs from text"""
        # URL pattern
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        urls = url_pattern.findall(text)

        # Filter for YouTube URLs
        youtube_urls = []
        for url in urls:
            if self.youtube_regex.search(url):
                youtube_urls.append(url)

        return youtube_urls

    def extract_video_id(self, url: str) -> str | None:
        """Extract video ID from YouTube URL"""
        try:
            if 'youtu.be' in url:
                return url.split('youtu.be/')[-1].split('?')[0]
            elif 'youtube.com' in url:
                parsed_url = urlparse(url)
                if 'v' in parse_qs(parsed_url.query):
                    return parse_qs(parsed_url.query)['v'][0]
                elif 'embed' in parsed_url.path:
                    return parsed_url.path.split('/embed/')[-1].split('?')[0]
                elif 'shorts' in parsed_url.path:
                    return parsed_url.path.split('/shorts/')[-1].split('?')[0]
                elif 'v/' in parsed_url.path:
                    return parsed_url.path.split('/v/')[-1].split('?')[0]
        except Exception:
            pass
        return None

    async def get_video_info(self, video_id: str) -> dict:
        """Get video information using multiple fallback methods"""
        url = f"https://www.youtube.com/watch?v={video_id}"

        # Method 1: Try pytube first
        try:
            logger.debug(f"Trying pytube for video {video_id}")
            youtube = pytube.YouTube(url)

            # SECURITY: Add timeout protection
            await asyncio.wait_for(
                asyncio.to_thread(youtube.check_availability),
                timeout=20.0  # 20 second timeout
            )

            return {
                "success": True,
                "title": youtube.title,
                "author": youtube.author,
                "length": youtube.length,
                "views": youtube.views,
                "publish_date": youtube.publish_date,
                "description": youtube.description[:500] if youtube.description else "",
                "url": url,
                "method": "pytube"
            }
        except Exception as e:
            logger.warning(f"Pytube failed for {video_id}: {type(e).__name__}, trying fallbacks")

        # Method 2: Try yt-dlp if available
        try:
            logger.debug(f"Trying yt-dlp fallback for video {video_id}")
            result = await self._extract_with_yt_dlp(video_id)
            if result["success"]:
                return result
        except Exception as e:
            logger.warning(f"yt-dlp fallback failed for {video_id}: {type(e).__name__}")

        # Method 3: Try YouTube Data API if key available
        try:
            logger.debug(f"Trying YouTube API fallback for video {video_id}")
            result = await self._extract_with_youtube_api(video_id)
            if result["success"]:
                return result
        except Exception as e:
            logger.warning(f"YouTube API fallback failed for {video_id}: {type(e).__name__}")

        # Method 4: Try basic HTML scraping
        try:
            logger.debug(f"Trying HTML scraping fallback for video {video_id}")
            result = await self._extract_with_html_scraping(video_id)
            if result["success"]:
                return result
        except Exception as e:
            logger.warning(f"HTML scraping fallback failed for {video_id}: {type(e).__name__}")

        logger.error(f"All video info extraction methods failed for {video_id}")
        return {"success": False, "error": "Failed to retrieve video information from all sources"}

    async def _extract_with_yt_dlp(self, video_id: str) -> dict:
        """Try to extract video info using yt-dlp (more reliable than pytube)"""
        try:
            import subprocess
            import json

            # Run yt-dlp to get video info
            cmd = [
                "yt-dlp",
                "--no-warnings",
                "--no-playlist",
                "--print-json",
                "--skip-download",
                f"https://www.youtube.com/watch?v={video_id}"
            ]

            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode == 0 and stdout:
                data = json.loads(stdout.decode())
                return {
                    "success": True,
                    "title": data.get("title", "Unknown Title"),
                    "author": data.get("uploader", "Unknown Author"),
                    "length": data.get("duration", 0),
                    "views": data.get("view_count", 0),
                    "publish_date": data.get("upload_date"),
                    "description": data.get("description", "")[:500],
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "method": "yt-dlp"
                }
        except (ImportError, FileNotFoundError):
            logger.debug("yt-dlp not available")
        except Exception as e:
            logger.error(f"yt-dlp extraction failed: {type(e).__name__}")

        return {"success": False, "error": "yt-dlp extraction failed"}

    async def _extract_with_youtube_api(self, video_id: str) -> dict:
        """Try to extract video info using YouTube Data API v3"""
        try:
            # Check if we have an API key configured
            api_key = getattr(self, '_youtube_api_key', None)
            if not api_key:
                return {"success": False, "error": "YouTube API key not configured"}

            api_url = f"https://www.googleapis.com/youtube/v3/videos"
            params = {
                "part": "snippet,statistics,contentDetails",
                "id": video_id,
                "key": api_key
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("items"):
                            video = data["items"][0]
                            snippet = video.get("snippet", {})
                            statistics = video.get("statistics", {})
                            content_details = video.get("contentDetails", {})

                            return {
                                "success": True,
                                "title": snippet.get("title", "Unknown Title"),
                                "author": snippet.get("channelTitle", "Unknown Author"),
                                "length": self._parse_duration(content_details.get("duration", "PT0S")),
                                "views": int(statistics.get("viewCount", 0)),
                                "publish_date": snippet.get("publishedAt"),
                                "description": snippet.get("description", "")[:500],
                                "url": f"https://www.youtube.com/watch?v={video_id}",
                                "method": "youtube_api"
                            }
        except Exception as e:
            logger.error(f"YouTube API extraction failed: {type(e).__name__}")

        return {"success": False, "error": "YouTube API extraction failed"}

    async def _extract_with_html_scraping(self, video_id: str) -> dict:
        """Try to extract basic video info from YouTube HTML"""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()

                        # Extract title from HTML
                        title = "Unknown Title"
                        title_match = re.search(r'<title>([^<]+)</title>', html)
                        if title_match:
                            title = title_match.group(1).replace(" - YouTube", "").strip()

                        # Extract author/channel
                        author = "Unknown Author"
                        author_match = re.search(r'"author":"([^"]+)"', html)
                        if author_match:
                            author = author_match.group(1)

                        # Extract view count
                        views = 0
                        view_match = re.search(r'"viewCount":"(\d+)"', html)
                        if view_match:
                            views = int(view_match.group(1))

                        return {
                            "success": True,
                            "title": title,
                            "author": author,
                            "length": 0,  # Can't easily extract from HTML
                            "views": views,
                            "publish_date": None,
                            "description": "",
                            "url": url,
                            "method": "html_scraping"
                        }
        except Exception as e:
            logger.error(f"HTML scraping extraction failed: {type(e).__name__}")

        return {"success": False, "error": "HTML scraping extraction failed"}

    def _parse_duration(self, duration: str) -> int:
        """Parse ISO 8601 duration to seconds"""
        import re
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            return hours * 3600 + minutes * 60 + seconds
        return 0

    async def get_transcript(self, video_id: str) -> dict:
        """Get transcript for YouTube video"""
        try:
            # Use the correct YouTubeTranscriptApi API
            yt_api = YouTubeTranscriptApi()
            transcripts = yt_api.list(video_id)

            # Find the best available transcript
            transcript = None
            transcripts_list = list(transcripts)

            if not transcripts_list:
                return {"success": False, "error": "No transcripts available for this video"}

            # Prefer English manual transcripts, then English auto-generated, then any available
            for t in transcripts_list:
                if t.language_code.startswith('en'):
                    if not t.is_generated:
                        transcript = t  # Manual English transcript
                        break
                    elif transcript is None or not transcript.language_code.startswith('en'):
                        transcript = t  # Auto-generated English transcript

            # If no English transcript, use any available
            if not transcript:
                transcript = transcripts_list[0]

            # Fetch the transcript data
            transcript_data = transcript.fetch()

            if not transcript_data:
                return {"success": False, "error": "Failed to fetch transcript data"}

            # Combine transcript text
            full_text = " ".join([entry.text for entry in transcript_data])

            return {
                "success": True,
                "text": full_text,
                "language": transcript.language,
                "is_generated": transcript.is_generated,
                "duration": sum([entry.duration for entry in transcript_data])
            }

        except Exception as e:
            logger.error(f"Error getting transcript for {video_id}: {type(e).__name__}")
            return {"success": False, "error": "Failed to retrieve transcript"}

    async def summarize_transcript(self, video_info: dict, transcript_data: dict) -> str:
        """Use AI to summarize video transcript"""
        if not transcript_data["success"]:
            return "❌ Could not retrieve video transcript."

        title = video_info.get("title", "Unknown")
        author = video_info.get("author", "Unknown")
        transcript = transcript_data["text"]

        # Truncate transcript if too long
        if len(transcript) > TRANSCRIPT_MAX_LENGTH:
            transcript = transcript[:TRANSCRIPT_MAX_LENGTH] + "..."

        prompt = f"""Please provide a comprehensive summary of the following YouTube video:

Title: {title}
Channel: {author}
Video Length: {video_info.get('length', 'Unknown')} seconds

Transcript:
{transcript}

Please provide:
1. A brief 2-3 sentence summary
2. Key topics and main points (bullet format)
3. Important quotes or takeaways if relevant
4. Overall theme or message

Keep it informative and well-structured."""

        try:
            summary = await self.ollama.generate(prompt)
            return summary
        except Exception as e:
            logger.error(f"Error generating transcript summary: {type(e).__name__}")
            return "❌ Failed to generate video summary."

    async def process_video(self, url: str) -> str:
        """Process a single YouTube video and return summary"""
        # Validate URL
        valid, validation_msg = self.validator.validate_url(url)
        if not valid:
            return f"❌ {validation_msg}"

        # Extract video ID
        video_id = self.extract_video_id(url)
        if not video_id:
            return "❌ Invalid YouTube URL."

        # Get video info
        video_info = await self.get_video_info(video_id)
        if not video_info["success"]:
            return f"❌ Could not retrieve video info: {video_info['error']}"

        # Get transcript
        transcript_data = await self.get_transcript(video_id)

        # Generate summary
        summary = await self.summarize_transcript(video_info, transcript_data)

        # Format response
        title = video_info["title"]
        author = video_info["author"]
        views = f"{video_info['views']:,}" if video_info.get("views") else "Unknown"
        length = f"{video_info.get('length', 0)//60}:{video_info.get('length', 0)%60:02d}" if video_info.get('length') else "Unknown"

        # Add extraction method info if not standard
        method_info = ""
        extraction_method = video_info.get("method", "pytube")
        if extraction_method != "pytube":
            method_info = f"🔧 *Extraction:* {extraction_method}\n"

        response = f"🎬 *{title}*\n\n"
        response += f"👤 *Channel:* {author}\n"
        response += f"👁️ *Views:* {views}\n"
        response += f"⏱️ *Duration:* {length}\n"
        if method_info:
            response += method_info
        response += f"🔗 *Video:* [Watch Now]({url})\n\n"

        # Add transcript availability info
        if transcript_data["success"]:
            response += f"📝 *Transcript:* Available ({transcript_data['language']})\n\n"
        else:
            response += f"📝 *Transcript:* {transcript_data['error']}\n\n"

        response += "📋 *Summary:*\n"
        response += summary

        # Validate final response
        if not response or len(response.strip()) == 0:
            return "❌ Failed to generate video summary: No content available."

        # Ensure response doesn't exceed Telegram limits
        if len(response) > 4000:
            response = response[:3950] + "\n\n*[Summary truncated due to length]*"

        return response
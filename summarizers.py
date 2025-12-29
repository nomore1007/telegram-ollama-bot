"""Content summarization classes for news articles and YouTube videos"""

import asyncio
import logging
import re
from urllib.parse import parse_qs, urlparse

from newspaper import Article
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import pytube

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

            # Check if this is a paywall/access issue - try archive.is fallback
            is_access_blocked = (
                "403" in str(e) or
                "forbidden" in str(e).lower() or
                "paywall" in str(e).lower() or
                "subscription" in str(e).lower()
            )

            if is_access_blocked:
                logger.info(f"Trying archive.is fallback for {url}")
                try:
                    archive_result = await self._extract_from_archive(url)
                    if archive_result["success"]:
                        logger.info(f"Successfully extracted article from archive.is for {url}")
                        return archive_result
                    else:
                        logger.warning(f"Archive.is fallback also failed for {url}")
                except Exception as archive_e:
                    logger.error(f"Archive.is fallback failed for {url}: {type(archive_e).__name__}")

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

    async def _extract_from_archive(self, url: str) -> dict:
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
        if article_data.get("source") == "archive.is":
            source_indicator = "📚 *Archived Content* (accessed via archive.is)\n"
            source_url = article_data.get("url", url)

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
        """Get video information using pytube"""
        try:
            youtube = pytube.YouTube(f"https://www.youtube.com/watch?v={video_id}")

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
                "url": f"https://www.youtube.com/watch?v={video_id}"
            }
        except Exception as e:
            logger.error(f"Error getting video info for {video_id}: {type(e).__name__}")
            return {"success": False, "error": "Failed to retrieve video information"}

    async def get_transcript(self, video_id: str) -> dict:
        """Get transcript for YouTube video"""
        try:
            # Try to get transcript in multiple languages
            transcript_list = await asyncio.to_thread(YouTubeTranscriptApi.list_transcripts, video_id)

            # Try English first, then any available language
            transcript = None
            languages = ['en', 'en-US', 'en-GB']

            for lang in languages:
                try:
                    transcript = await asyncio.to_thread(transcript_list.find_transcript, [lang])
                    break
                except:
                    continue

            # If no English transcript, get any manually created transcript
            if not transcript:
                try:
                    transcript = await asyncio.to_thread(transcript_list.find_manually_created_transcript)
                except:
                    # Fall back to any available transcript
                    try:
                        transcript = await asyncio.to_thread(list(transcript_list).__getitem__, 0)
                    except:
                        pass

            if not transcript:
                return {"success": False, "error": "No transcript available"}

            # Fetch transcript data
            transcript_data = await asyncio.to_thread(transcript.fetch)

            # Combine transcript text
            full_text = " ".join([entry['text'] for entry in transcript_data])

            return {
                "success": True,
                "text": full_text,
                "language": transcript.language,
                "is_generated": transcript.is_generated,
                "duration": sum([entry['duration'] for entry in transcript_data])
            }

        except (TranscriptsDisabled, NoTranscriptFound) as e:
            return {"success": False, "error": "Transcript not available for this video"}
        except Exception as e:
            logger.error(f"Error getting transcript for {video_id}: {type(e).__name__}")
            return {"success": False, "error": "Failed to retrieve video transcript"}

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

        response = f"🎬 *{title}*\n\n"
        response += f"👤 *Channel:* {author}\n"
        response += f"👁️ *Views:* {views}\n"
        response += f"⏱️ *Duration:* {length}\n"
        response += f"🔗 *Video:* [Watch Now]({url})\n\n"

        # Add transcript availability info
        if transcript_data["success"]:
            response += f"📝 *Transcript:* Available ({transcript_data['language']})\n\n"
        else:
            response += f"📝 *Transcript:* {transcript_data['error']}\n\n"

        response += "📋 *Summary:*\n"
        response += summary

        return response
#!/usr/bin/env python3
"""
Admin Management CLI Tool for Deepthought Bot

This script allows managing bot administrators from the command line,
useful for initial setup and maintenance.
"""

import argparse
import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from admin import AdminManager


def load_admin_manager():
    """Load admin manager from current settings."""
    # Try to load from settings.py or settings.example.py
    admin_ids = []

    settings_files = ['settings.py', 'settings.example.py']
    for settings_file in settings_files:
        if os.path.exists(settings_file):
            try:
                # Simple settings parsing (not full Python execution for security)
                with open(settings_file, 'r') as f:
                    content = f.read()

                # Extract ADMIN_USER_IDS line
                for line in content.split('\n'):
                    if 'ADMIN_USER_IDS' in line and '=' in line:
                        # Simple parsing of list format
                        try:
                            value_part = line.split('=')[1].strip()
                            if '[' in value_part and ']' in value_part:
                                # Extract numbers from list
                                import re
                                numbers = re.findall(r'\d+', value_part)
                                admin_ids = [int(n) for n in numbers]
                                break
                        except:
                            continue
            except Exception as e:
                print(f"Warning: Could not parse {settings_file}: {e}")
                continue

    return AdminManager(admin_ids)


def save_admin_config(admin_manager, settings_file='settings.py'):
    """Save current admin configuration to settings file."""
    admin_list = list(admin_manager.get_admins())
    admin_str = str(admin_list)

    if os.path.exists(settings_file):
        # Read current content
        with open(settings_file, 'r') as f:
            content = f.read()

        # Replace or add ADMIN_USER_IDS line
        lines = content.split('\n')
        admin_line_found = False

        for i, line in enumerate(lines):
            if 'ADMIN_USER_IDS' in line and '=' in line:
                lines[i] = f'ADMIN_USER_IDS: list = {admin_str}'
                admin_line_found = True
                break

        if not admin_line_found:
            # Add after other configuration lines
            for i, line in enumerate(lines):
                if line.startswith('ENABLED_PLUGINS'):
                    lines.insert(i + 1, f'ADMIN_USER_IDS: list = {admin_str}')
                    admin_line_found = True
                    break

        if not admin_line_found:
            lines.append(f'ADMIN_USER_IDS: list = {admin_str}')

        # Write back
        with open(settings_file, 'w') as f:
            f.write('\n'.join(lines))

        print(f"✅ Updated {settings_file}")
    else:
        print(f"❌ Settings file {settings_file} not found")


def main():
    parser = argparse.ArgumentParser(description='Deepthought Bot Admin Management CLI')
    parser.add_argument('--settings', '-s', default='settings.py',
                       help='Settings file to use (default: settings.py)')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Add admin command
    add_parser = subparsers.add_parser('add', help='Add an administrator')
    add_parser.add_argument('user_id', type=int, help='Telegram user ID to add as admin')

    # Remove admin command
    remove_parser = subparsers.add_parser('remove', help='Remove an administrator')
    remove_parser.add_argument('user_id', type=int, help='Telegram user ID to remove from admins')

    # List admins command
    subparsers.add_parser('list', help='List all administrators')

    # Setup command for initial configuration
    setup_parser = subparsers.add_parser('setup', help='Initial admin setup')
    setup_parser.add_argument('user_id', type=int, help='Your Telegram user ID for initial admin setup')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Load admin manager
    admin_manager = load_admin_manager()

    if args.command == 'add':
        if admin_manager.add_admin(args.user_id, force=True):
            print(f"✅ Added admin: {args.user_id}")
            save_admin_config(admin_manager, args.settings)
        else:
            print(f"❌ Failed to add admin: {args.user_id}")

    elif args.command == 'remove':
        if admin_manager.remove_admin(args.user_id, force=True):
            print(f"✅ Removed admin: {args.user_id}")
            save_admin_config(admin_manager, args.settings)
        else:
            print(f"❌ Failed to remove admin: {args.user_id}")

    elif args.command == 'list':
        admins = admin_manager.get_admins()
        if admins:
            print("👑 Current Administrators:")
            for admin_id in admins:
                print(f"  • {admin_id}")
        else:
            print("❌ No administrators configured")

    elif args.command == 'setup':
        if admin_manager.add_admin(args.user_id, force=True):
            print("🎉 Initial admin setup complete!")
            print(f"👑 Admin user ID: {args.user_id}")
            print("💡 You can now use admin commands in Telegram/Discord")
            print("💡 Use this script to manage admins: python admin_cli.py --help")
            save_admin_config(admin_manager, args.settings)
        else:
            print(f"❌ Setup failed for user ID: {args.user_id}")


if __name__ == '__main__':
    main()
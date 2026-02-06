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
import re # Added for parsing ADMIN_USER_IDS

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from admin import AdminManager
from settings_manager import settings_manager, settings, config # Import config


def load_admin_manager():
    """Load admin manager from current configuration."""
    # SettingsManager already handles loading from config.py and environment variables
    admin_ids = config.ADMIN_USER_IDS if isinstance(config.ADMIN_USER_IDS, list) else []
    return AdminManager(admin_ids)


def save_admin_config(admin_manager):
    """Save current admin configuration to config.py file."""
    admin_list = list(admin_manager.get_admins())
    admin_str = str(admin_list) # e.g., '[123, 456]'

    config_file_path = config.BOT_CONFIG_DIR / 'config.py'

    if config_file_path.exists():
        # Read current content
        with open(config_file_path, 'r') as f:
            content = f.read()

        # Replace or add ADMIN_USER_IDS line
        lines = content.split('\n')
        admin_line_found = False

        for i, line in enumerate(lines):
            # Use regex to find ADMIN_USER_IDS line, accounting for potential type hints and spacing
            if re.match(r'ADMIN_USER_IDS\s*:\s*List\[int\]\s*=\s*\[.*\]', line) or re.match(r'ADMIN_USER_IDS\s*=\s*\[.*\]', line):
                lines[i] = f'ADMIN_USER_IDS: List[int] = {admin_str}'
                admin_line_found = True
                break

        if not admin_line_found:
            # If not found, try to add it after other configuration lines
            # Find a suitable place, e.g., after BOT_USERNAME or DEFAULT_PROMPT
            insert_index = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('DEFAULT_PROMPT'):
                    insert_index = i + 1
                    break
            if insert_index != -1:
                lines.insert(insert_index, f'ADMIN_USER_IDS: List[int] = {admin_str}')
            else:
                lines.append(f'ADMIN_USER_IDS: List[int] = {admin_str}') # Add at the end if no suitable place found

        # Write back
        with open(config_file_path, 'w') as f:
            f.write('\n'.join(lines))

        print(f"✅ Updated {config_file_path.name}")
    else:
        print(f"❌ Configuration file {config_file_path.name} not found. Admins were updated in memory but not saved persistently.")
        print(f"💡 Please ensure '{config_file_path.name}' exists in '{config.BOT_CONFIG_DIR}' if you want to save changes persistently.")


def main():
    parser = argparse.ArgumentParser(description='Deepthought Bot Admin Management CLI')
    # Removed --settings argument as config.py is now the default managed file

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
            save_admin_config(admin_manager) # Removed settings file arg
        else:
            print(f"❌ Failed to add admin: {args.user_id}")

    elif args.command == 'remove':
        if admin_manager.remove_admin(args.user_id, force=True):
            print(f"✅ Removed admin: {args.user_id}")
            save_admin_config(admin_manager) # Removed settings file arg
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
            save_admin_config(admin_manager) # Removed settings file arg
        else:
            print(f"❌ Setup failed for user ID: {args.user_id}")


if __name__ == '__main__':
    main()
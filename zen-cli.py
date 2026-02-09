#!/usr/bin/env python3
"""Zen AI Pentest CLI

Main entry point for command-line operations:
- API Key management
- Configuration
- Scan operations
"""

import sys
import argparse
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.api_key_manager import APIKeyManager


def cmd_apikey(args):
    """Handle API key commands"""
    manager = APIKeyManager()

    if args.apikey_action == "create":
        if not args.name:
            print("Error: --name required for key creation")
            return 1

        key_id, plain_key = manager.generate_key(
            name=args.name, permissions=args.permissions or ["read"], created_by=args.user or "cli"
        )

        print("=" * 60)
        print("API Key Created Successfully")
        print("=" * 60)
        print(f"Key ID:    {key_id}")
        print(f"API Key:   {plain_key}")
        print(f"Name:      {args.name}")
        print(f"Permissions: {', '.join(args.permissions or ['read'])}")
        print("=" * 60)
        print("⚠️  WARNING: Save this key now - it will NOT be shown again!")
        print("=" * 60)

    elif args.apikey_action == "list":
        keys = manager.list_keys()

        if not keys:
            print("No API keys found")
            return 0

        print(f"{'Key ID':<35} {'Name':<20} {'Status':<10} {'Expires':<20}")
        print("-" * 85)

        for key in keys:
            expires = key.expires_at[:10] if key.expires_at else "Never"
            print(f"{key.key_id:<35} {key.name:<20} {key.status:<10} {expires:<20}")

        print(f"\nTotal: {len(keys)} keys")

    elif args.apikey_action == "revoke":
        if not args.key_id:
            print("Error: --key-id required")
            return 1

        if manager.revoke_key(args.key_id, args.user or "cli"):
            print(f"✓ Key {args.key_id} revoked successfully")
        else:
            print(f"✗ Key {args.key_id} not found")
            return 1

    elif args.apikey_action == "rotate":
        if not args.key_id:
            print("Error: --key-id required")
            return 1

        result = manager.rotate_key(args.key_id, args.user or "cli")
        if result:
            new_id, new_key = result
            print("=" * 60)
            print("Key Rotated Successfully")
            print("=" * 60)
            print(f"Old Key ID: {args.key_id}")
            print(f"New Key ID: {new_id}")
            print(f"New Key:    {new_key}")
            print("=" * 60)
            print("⚠️  WARNING: Save the new key now - it will NOT be shown again!")
            print("=" * 60)
        else:
            print(f"✗ Key {args.key_id} not found")
            return 1

    elif args.apikey_action == "audit":
        logs = manager.get_audit_log(args.key_id, limit=args.limit or 20)

        if not logs:
            print("No audit entries found")
            return 0

        print(f"{'Timestamp':<25} {'Action':<20} {'Key ID':<20} {'Status'}")
        print("-" * 85)

        for log in logs:
            status = "✓" if log.success else "✗"
            key_id_short = log.key_id[:17] + "..." if len(log.key_id) > 20 else log.key_id
            print(f"{log.timestamp[:25]:<25} {log.action:<20} {key_id_short:<20} {status}")

    return 0


def cmd_config(args):
    """Handle configuration commands"""
    print("Configuration management")
    print("(Implementation in progress)")
    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(prog="zen-cli", description="Zen AI Pentest Command Line Interface")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # API Key management
    apikey_parser = subparsers.add_parser("apikey", help="API Key management")
    apikey_parser.add_argument("apikey_action", choices=["create", "list", "revoke", "rotate", "audit"], help="API key action")
    apikey_parser.add_argument("--name", help="Key name")
    apikey_parser.add_argument("--key-id", help="Key ID for operations")
    apikey_parser.add_argument("--permissions", nargs="+", help="Key permissions")
    apikey_parser.add_argument("--user", default="cli", help="User performing action")
    apikey_parser.add_argument("--limit", type=int, help="Limit for audit logs")

    # Configuration
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_parser.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"), help="Set config value")
    config_parser.add_argument("--get", metavar="KEY", help="Get config value")

    args = parser.parse_args()

    if args.command == "apikey":
        return cmd_apikey(args)
    elif args.command == "config":
        return cmd_config(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())

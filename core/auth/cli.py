#!/usr/bin/env python3
"""
Auth CLI commands for Zen-AI-Pentest
Provides 'zen auth login' similar to 'gh auth login'
"""

import asyncio
import sys

from .device_flow import AuthenticationError, DeviceCodeFlow
from .token_store import TokenStore


class AuthCLI:
    """Authentication CLI interface"""

    def __init__(self):
        self.token_store = TokenStore()

    def login(self, interactive: bool = True) -> int:
        """
        Authenticate with Kimi AI using device code flow

        Usage: zen auth login
        """
        print("🔐 Zen AI Authentication")
        print("=" * 50)
        print()

        # Check if already logged in
        if self.token_store.is_authenticated():
            print("✅ Already authenticated!")
            print(f"   Credentials stored at: {self.token_store.get_credential_path()}")
            print()
            response = input("Do you want to re-authenticate? [y/N]: ").strip().lower()
            if response != "y":
                print("Keeping existing credentials.")
                return 0
            print()

        try:
            # Run device flow
            return asyncio.run(self._do_login())
        except KeyboardInterrupt:
            print("\n\n❌ Authentication cancelled.")
            return 130
        except Exception as e:
            print(f"\n❌ Authentication failed: {e}")
            return 1

    async def _do_login(self) -> int:
        """Perform the actual login flow"""
        async with DeviceCodeFlow() as flow:
            # Step 1: Get device code
            print("🔄 Requesting device code...")
            try:
                device_data = await flow.initiate_device_flow()
            except AuthenticationError as e:
                print(f"❌ {e}")
                print()
                print("Falling back to API key authentication...")
                return self._manual_api_key_login()

            user_code = device_data.get("user_code")
            verification_uri = device_data.get("verification_uri")
            device_code = device_data.get("device_code")
            interval = device_data.get("interval", 5)

            # Step 2: Show instructions to user
            print()
            print("📋 Authentication Instructions:")
            print("-" * 50)
            print(f"1. Open: {verification_uri}")
            print(f"2. Enter code: {user_code}")
            print()

            # Try to open browser automatically
            if flow.open_browser(verification_uri):
                print("🌐 Browser opened automatically!")
            else:
                print("⚠️  Please open the URL manually in your browser.")

            print()
            print("⏳ Waiting for authentication...")
            print("   (Press Ctrl+C to cancel)")
            print()

            # Step 3: Poll for token
            try:
                token_data = await flow.poll_for_token(device_code=device_code, interval=interval)
            except AuthenticationError as e:
                print(f"❌ {e}")
                return 1

            # Step 4: Save credentials
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in")

            self.token_store.save_credentials(
                access_token=access_token, refresh_token=refresh_token, expires_in=expires_in, provider="kimi"
            )

            print("✅ Successfully authenticated!")
            print(f"   Credentials saved to: {self.token_store.get_credential_path()}")
            print()
            print("You can now use Zen AI without providing an API key.")
            return 0

    def _manual_api_key_login(self) -> int:
        """Fallback: Manual API key entry"""
        print()
        print("📝 Manual API Key Authentication")
        print("-" * 50)
        print()
        print("Please enter your Kimi AI API key.")
        print("You can find it at: https://platform.moonshot.cn/")
        print()

        api_key = input("API Key: ").strip()

        if not api_key:
            print("❌ No API key provided.")
            return 1

        if not api_key.startswith(("sk-", "Bearer ")):
            print("⚠️  Warning: API key doesn't match expected format (should start with 'sk-')")
            confirm = input("Continue anyway? [y/N]: ").strip().lower()
            if confirm != "y":
                return 1

        # Save as access token
        self.token_store.save_credentials(access_token=api_key, refresh_token=None, expires_in=None, provider="kimi")

        print()
        print("✅ API key saved!")
        print(f"   Credentials stored at: {self.token_store.get_credential_path()}")
        return 0

    def logout(self) -> int:
        """
        Remove authentication credentials

        Usage: zen auth logout
        """
        print("🚪 Zen AI Logout")
        print("=" * 50)
        print()

        if not self.token_store.is_authenticated():
            print("ℹ️  Not currently authenticated.")
            return 0

        confirm = input("Are you sure you want to log out? [y/N]: ").strip().lower()

        if confirm != "y":
            print("Logout cancelled.")
            return 0

        self.token_store.clear_credentials()
        print("✅ Successfully logged out.")
        print("   Credentials have been removed.")
        return 0

    def status(self) -> int:
        """
        Check authentication status

        Usage: zen auth status
        """
        print("📊 Authentication Status")
        print("=" * 50)
        print()

        creds = self.token_store.load_credentials()

        if not creds:
            print("❌ Not authenticated")
            print()
            print("Run 'zen auth login' to authenticate.")
            return 1

        print("✅ Authenticated")
        print()
        print(f"   Provider: {creds.get('provider', 'unknown')}")
        print(f"   Credentials: {self.token_store.get_credential_path()}")

        created_at = creds.get("created_at")
        if created_at:
            print(f"   Created: {created_at}")

        expires_at = creds.get("expires_at")
        if expires_at:
            from datetime import datetime

            expiry = datetime.fromisoformat(expires_at)
            now = datetime.utcnow()

            if now > expiry:
                print(f"   Expires: {expires_at} (⚠️  EXPIRED)")
            else:
                remaining = expiry - now
                hours = remaining.total_seconds() / 3600
                print(f"   Expires: {expires_at} (in {hours:.1f} hours)")
        else:
            print("   Expires: Never (API key)")

        print()
        print("Run 'zen auth logout' to remove credentials.")
        return 0

    def print_help(self):
        """Print auth command help"""
        help_text = """
🔐 Authentication Commands:

  zen auth login    - Authenticate with Kimi AI (opens browser)
  zen auth logout   - Remove stored credentials
  zen auth status   - Check authentication status

Examples:
  $ zen auth login
  # Opens browser for authentication
  # No API key needed after login!

  $ zen auth status
  # Shows current authentication status

  $ zen auth logout
  # Removes stored credentials

Notes:
  - Credentials are stored securely in your OS keychain/config
  - After login, all commands use the stored token automatically
  - Tokens are automatically refreshed when they expire
        """
        print(help_text)


def main():
    """Entry point for 'zen auth' command"""
    import sys

    cli = AuthCLI()

    if len(sys.argv) < 2:
        cli.print_help()
        return 0

    command = sys.argv[1].lower()

    if command == "login":
        return cli.login()
    elif command == "logout":
        return cli.logout()
    elif command == "status":
        return cli.status()
    else:
        cli.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Discord Server Berechtigungs-Setup
Konfiguriert automatisch die Sicherheitseinstellungen für den Discord-Server
"""

import argparse
import asyncio
import os

# Discord.py prüfen
try:
    import discord
    from discord.ext import commands

    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    print(
        "⚠️  discord.py nicht installiert. Installiere mit: pip install discord.py"
    )


# Farben für Terminal
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"


def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")


class DiscordSecuritySetup:
    """Automatisches Setup der Discord-Server-Sicherheit"""

    def __init__(self, token=None):
        self.token = token
        self.bot = None
        self.intents = discord.Intents.default()
        self.intents.guilds = True
        self.intents.members = True

    async def setup_bot(self):
        """Initialisiert den Bot"""
        if not self.token:
            print_error("Kein Bot-Token angegeben!")
            return False

        self.bot = commands.Bot(command_prefix="!", intents=self.intents)

        @self.bot.event
        async def on_ready():
            print_success(f"Bot eingeloggt als {self.bot.user}")

        try:
            await self.bot.start(self.token)
            return True
        except Exception as e:
            print_error(f"Bot-Login fehlgeschlagen: {e}")
            return False

    async def configure_server_security(self, guild_id=None):
        """Konfiguriert die Server-Sicherheit"""
        if not self.bot:
            print_error("Bot nicht initialisiert!")
            return False

        # Guild finden
        if guild_id:
            guild = self.bot.get_guild(int(guild_id))
        else:
            guilds = self.bot.guilds
            if len(guilds) == 0:
                print_error("Bot ist auf keinem Server!")
                return False
            elif len(guilds) == 1:
                guild = guilds[0]
            else:
                print_info("Mehrere Server gefunden:")
                for i, g in enumerate(guilds):
                    print(f"  {i+1}. {g.name} (ID: {g.id})")
                choice = int(input("Wähle Server (Nummer): ")) - 1
                guild = guilds[choice]

        if not guild:
            print_error("Server nicht gefunden!")
            return False

        print_info(f"Konfiguriere Server: {guild.name}")

        try:
            # 1. @everyone Rolle einschränken
            everyone = guild.default_role
            await everyone.edit(
                permissions=discord.Permissions.none(),
                reason="Sicherheits-Setup: @everyone einschränken",
            )
            print_success(
                "@everyone Rolle eingeschränkt (keine Berechtigungen)"
            )

            # 2. Member Rolle erstellen oder updaten
            member_role = discord.utils.get(guild.roles, name="Member")
            member_perms = discord.Permissions(
                # Textkanäle
                read_messages=True,
                send_messages=True,
                read_message_history=True,
                embed_links=True,
                attach_files=True,
                use_external_emojis=True,
                add_reactions=True,
                use_application_commands=True,
                # Sprachkanäle
                connect=True,
                speak=True,
                use_voice_activation=True,
                stream=True,
                video=True,
            )

            if member_role:
                await member_role.edit(
                    permissions=member_perms,
                    reason="Sicherheits-Setup: Member-Rolle aktualisieren",
                )
                print_success("Member-Rolle aktualisiert")
            else:
                member_role = await guild.create_role(
                    name="Member",
                    permissions=member_perms,
                    color=discord.Color.blue(),
                    hoist=True,
                    reason="Sicherheits-Setup: Member-Rolle erstellen",
                )
                print_success("Member-Rolle erstellt")

            # 3. Moderator Rolle erstellen (optional)
            mod_role = discord.utils.get(guild.roles, name="Moderator")
            if not mod_role:
                mod_perms = discord.Permissions(
                    # Alles was Member hat
                    read_messages=True,
                    send_messages=True,
                    read_message_history=True,
                    embed_links=True,
                    attach_files=True,
                    use_external_emojis=True,
                    add_reactions=True,
                    connect=True,
                    speak=True,
                    use_voice_activation=True,
                    stream=True,
                    video=True,
                    # Moderator-Extras
                    kick_members=True,
                    moderate_members=True,  # Timeout
                    manage_messages=True,
                    manage_nicknames=True,
                )
                mod_role = await guild.create_role(
                    name="Moderator",
                    permissions=mod_perms,
                    color=discord.Color.orange(),
                    hoist=True,
                    reason="Sicherheits-Setup: Moderator-Rolle erstellen",
                )
                print_success("Moderator-Rolle erstellt")

            # 4. Allen Mitgliedern die Member-Rolle geben
            print_info("Weise Member-Rolle zu...")
            count = 0
            for member in guild.members:
                if not member.bot and member_role not in member.roles:
                    try:
                        await member.add_roles(
                            member_role, reason="Sicherheits-Setup"
                        )
                        count += 1
                    except Exception:
                        pass
            print_success(f"Member-Rolle an {count} Mitglieder vergeben")

            # 5. Channel-Berechtigungen prüfen
            print_info("Prüfe Channel-Berechtigungen...")
            for channel in guild.channels:
                # Entferne @everyone Überschreibungen
                overwrites = channel.overwrites
                if everyone in overwrites:
                    await channel.set_permissions(
                        everyone,
                        overwrite=None,
                        reason="Sicherheits-Setup: @everyone entfernen",
                    )

                # Füge Member-Rolle hinzu wenn nicht vorhanden
                if member_role not in overwrites:
                    await channel.set_permissions(
                        member_role,
                        read_messages=True,
                        send_messages=True,
                        connect=True,
                        speak=True,
                        reason="Sicherheits-Setup: Member-Rolle hinzufügen",
                    )

            print_success("Channel-Berechtigungen aktualisiert")

            # 6. Rollen-Hierarchie anpassen (Bot-Rolle muss über Member sein)
            bot_member = guild.get_member(self.bot.user.id)
            if bot_member:
                bot_role = bot_member.top_role
                if bot_role.position <= member_role.position:
                    print_warning(
                        "Bot-Rolle muss über Member-Rolle in der Hierarchie sein!"
                    )
                    print_info(
                        "Bitte manuell in Servereinstellungen → Rollen anpassen"
                    )

            print("\n" + "=" * 50)
            print_success("SICHERHEITS-SETUP ABGESCHLOSSEN!")
            print("=" * 50)
            print("\nZusammenfassung:")
            print(
                "  • @everyone: Keine Berechtigungen (Nicht-Mitglieder sehen nichts)"
            )
            print("  • Member-Rolle: Basis-Rechte ohne Admin-Funktionen")
            print("  • Moderator-Rolle: Kick, Timeout, Nachrichten löschen")
            print("  • Admin-Rolle: Unverändert (hat alle Rechte)")
            print("\nWichtig: Passe die Rollen-Hierarchie manuell an!")

            return True

        except discord.Forbidden:
            print_error("Bot hat nicht genügend Berechtigungen!")
            print_info(
                "Der Bot braucht: 'Server verwalten', 'Rollen verwalten', 'Kanäle verwalten'"
            )
            return False
        except Exception as e:
            print_error(f"Fehler: {e}")
            return False

    async def run(self, guild_id=None):
        """Hauptfunktion"""
        print("\n" + "=" * 50)
        print("🔒 DISCORD SERVER SICHERHEITS-SETUP")
        print("=" * 50 + "\n")

        if not await self.setup_bot():
            return False

        return await self.configure_server_security(guild_id)

    async def close(self):
        """Beendet den Bot"""
        if self.bot:
            await self.bot.close()


def manual_setup_guide():
    """Zeigt die manuelle Setup-Anleitung"""
    print("\n" + "=" * 50)
    print("📖 MANUELLE SETUP-ANLEITUNG")
    print("=" * 50 + "\n")

    steps = [
        ("Schritt 1", "Öffne Discord → Server-Einstellungen → Rollen"),
        ("Schritt 2", "Bearbeite @everyone:"),
        ("  • DEAKTIVIERE 'Kanäle sehen'"),
        ("  • DEAKTIVIERE 'Nachrichten senden'"),
        ("  • DEAKTIVIERE ALLE Admin-Berechtigungen"),
        ("Schritt 3", "Erstelle 'Member' Rolle:"),
        ("  • AKTIVIERE 'Kanäle sehen'"),
        ("  • AKTIVIERE 'Nachrichten senden'"),
        ("  • AKTIVIERE 'Nachrichtenverlauf lesen'"),
        ("  • AKTIVIERE 'Verbinden' (Voice)"),
        ("  • AKTIVIERE 'Sprechen' (Voice)"),
        ("  • DEAKTIVIERE 'Server verwalten'"),
        ("  • DEAKTIVIERE 'Rollen verwalten'"),
        ("  • DEAKTIVIERE 'Kanäle verwalten'"),
        ("Schritt 4", "Weise allen Mitgliedern die Member-Rolle zu"),
        (
            "Schritt 5",
            "Prüfe jeden Channel: Entferne @everyone, füge Member hinzu",
        ),
    ]

    for title, content in steps:
        print(f"\n{Colors.BLUE}{title}:{Colors.END}")
        for line in content.split("\n"):
            print(f"  {line}")

    print("\n" + "=" * 50)
    print("Detaillierte Anleitung:")
    print("  docs/DISCORD_SERVER_SETUP.md")
    print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Discord Server Sicherheits-Setup"
    )
    parser.add_argument("--token", "-t", help="Discord Bot Token")
    parser.add_argument("--guild", "-g", help="Discord Server ID (optional)")
    parser.add_argument(
        "--manual", "-m", action="store_true", help="Zeige manuelle Anleitung"
    )

    args = parser.parse_args()

    if args.manual or not DISCORD_AVAILABLE:
        manual_setup_guide()
        return

    # Token aus Argumenten oder Umgebung
    token = args.token or os.getenv("DISCORD_BOT_TOKEN")

    if not token:
        print_error("Kein Bot-Token angegeben!")
        print_info("Optionen:")
        print("  1. python setup_discord_permissions.py --token DEIN_TOKEN")
        print("  2. export DISCORD_BOT_TOKEN='dein_token'")
        print("  3. python setup_discord_permissions.py --manual")
        return

    # Setup ausführen
    setup = DiscordSecuritySetup(token)
    try:
        asyncio.run(setup.run(args.guild))
    except KeyboardInterrupt:
        print("\n" + print_warning("Abgebrochen durch Benutzer"))
    finally:
        asyncio.run(setup.close())


if __name__ == "__main__":
    main()

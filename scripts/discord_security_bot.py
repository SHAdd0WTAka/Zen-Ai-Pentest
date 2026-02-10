#!/usr/bin/env python3
"""
Discord Security Bot - Automatische Server-Konfiguration
Dieser Bot konfiguriert Discord-Server mit sicheren Standard-Berechtigungen
"""

import os
import asyncio
import discord
from discord.ext import commands
from discord import app_commands

# Bot-Intents
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Farben
EMBED_COLOR = discord.Color.blue()
SUCCESS_COLOR = discord.Color.green()
ERROR_COLOR = discord.Color.red()
WARNING_COLOR = discord.Color.orange()

@bot.event
async def on_ready():
    """Wird aufgerufen wenn der Bot bereit ist"""
    print(f'🤖 {bot.user} ist online!')
    print(f'📊 Auf {len(bot.guilds)} Servern aktiv')
    
    # Sync Slash Commands
    try:
        synced = await bot.tree.sync()
        print(f'✅ {len(synced)} Slash-Commands synchronisiert')
    except Exception as e:
        print(f'❌ Sync fehlgeschlagen: {e}')

@bot.tree.command(name="zen-security-setup", description="🔒 Konfiguriert Server-Sicherheit (Nur für Admins)")
@app_commands.checks.has_permissions(administrator=True)
async def security_setup(interaction: discord.Interaction):
    """
    Automatisches Sicherheits-Setup für den Discord-Server
    - @everyone: Keine Berechtigungen
    - Member-Rolle: Basis-Rechte ohne Admin-Funktionen
    """
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    progress_msg = await interaction.followup.send("🔒 Starte Sicherheits-Setup...", ephemeral=True)
    
    try:
        updates = []
        
        # 1. @everyone Rolle einschränken
        everyone = guild.default_role
        await everyone.edit(
            permissions=discord.Permissions.none(),
            reason=f"Sicherheits-Setup durch {interaction.user}"
        )
        updates.append("✅ @everyone: Alle Berechtigungen entfernt")
        await progress_msg.edit(content="\n".join(updates))
        
        # 2. Member Rolle erstellen/updaten
        member_role = discord.utils.get(guild.roles, name="Member")
        member_perms = discord.Permissions(
            # Text
            read_messages=True,
            send_messages=True,
            read_message_history=True,
            embed_links=True,
            attach_files=True,
            use_external_emojis=True,
            add_reactions=True,
            use_application_commands=True,
            # Voice
            connect=True,
            speak=True,
            use_voice_activation=True,
            stream=True,
            video=True,
        )
        
        if member_role:
            await member_role.edit(
                permissions=member_perms,
                reason=f"Sicherheits-Setup durch {interaction.user}"
            )
            updates.append("✅ Member-Rolle: Berechtigungen aktualisiert")
        else:
            member_role = await guild.create_role(
                name="Member",
                permissions=member_perms,
                color=discord.Color.blue(),
                hoist=True,
                reason=f"Sicherheits-Setup durch {interaction.user}"
            )
            updates.append("✅ Member-Rolle: Neu erstellt")
        
        await progress_msg.edit(content="\n".join(updates))
        
        # 3. Moderator Rolle (optional)
        mod_role = discord.utils.get(guild.roles, name="Moderator")
        if not mod_role:
            mod_perms = discord.Permissions(
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
                kick_members=True,
                moderate_members=True,
                manage_messages=True,
                manage_nicknames=True,
            )
            mod_role = await guild.create_role(
                name="Moderator",
                permissions=mod_perms,
                color=discord.Color.orange(),
                hoist=True,
                reason=f"Sicherheits-Setup durch {interaction.user}"
            )
            updates.append("✅ Moderator-Rolle: Neu erstellt")
            await progress_msg.edit(content="\n".join(updates))
        
        # 4. Mitgliedern Member-Rolle zuweisen
        count = 0
        for member in guild.members:
            if not member.bot and member_role not in member.roles:
                try:
                    await member.add_roles(member_role, reason="Sicherheits-Setup")
                    count += 1
                except:
                    pass
        
        if count > 0:
            updates.append(f"✅ {count} Mitgliedern die Member-Rolle zugewiesen")
            await progress_msg.edit(content="\n".join(updates))
        
        # 5. Channel-Berechtigungen aktualisieren
        channel_updates = 0
        for channel in guild.channels:
            overwrites = channel.overwrites
            
            # Entferne @everyone
            if everyone in overwrites:
                await channel.set_permissions(
                    everyone,
                    overwrite=None,
                    reason=f"Sicherheits-Setup durch {interaction.user}"
                )
            
            # Füge Member-Rolle hinzu
            if member_role not in overwrites:
                await channel.set_permissions(
                    member_role,
                    read_messages=True,
                    send_messages=isinstance(channel, discord.TextChannel),
                    connect=isinstance(channel, discord.VoiceChannel),
                    speak=isinstance(channel, discord.VoiceChannel),
                    reason=f"Sicherheits-Setup durch {interaction.user}"
                )
                channel_updates += 1
        
        updates.append(f"✅ {channel_updates} Channels aktualisiert")
        await progress_msg.edit(content="\n".join(updates))
        
        # 6. Rollen-Hierarchie Warnung
        bot_member = guild.get_member(bot.user.id)
        if bot_member:
            bot_role = bot_member.top_role
            if bot_role.position <= member_role.position:
                updates.append("⚠️ Bot-Rolle muss über Member-Rolle sein!")
                updates.append("   → Passe in Servereinstellungen → Rollen an")
        
        # Fertig!
        embed = discord.Embed(
            title="🔒 Sicherheits-Setup Abgeschlossen!",
            description="Der Server ist jetzt sicher konfiguriert.",
            color=SUCCESS_COLOR
        )
        
        embed.add_field(
            name="@everyone (Nicht-Mitglieder)",
            value="```❌ Keine Berechtigungen\n❌ Kann nichts sehen\n❌ Kein Zugriff auf Channels```",
            inline=False
        )
        
        embed.add_field(
            name="Member (Normale Mitglieder)",
            value="```✅ Kanäle sehen\n✅ Nachrichten senden\n✅ Voice-Chat\n❌ Keine Server-Einstellungen\n❌ Kein Kick/Ban```",
            inline=False
        )
        
        embed.add_field(
            name="Moderator",
            value="```✅ Alles wie Member\n✅ Nachrichten löschen\n✅ Timeout vergeben\n✅ Mitglieder kicken\n❌ Keine Server-Einstellungen```",
            inline=False
        )
        
        embed.add_field(
            name="Admin",
            value="```✅ Alle Berechtigungen\n✅ Server verwalten\n✅ Rollen/Kanäle verwalten```",
            inline=False
        )
        
        embed.set_footer(text=f"Setup durchgeführt von {interaction.user}")
        
        await progress_msg.delete()
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except discord.Forbidden:
        await progress_msg.edit(content="❌ Fehler: Bot hat nicht genügend Berechtigungen!")
    except Exception as e:
        await progress_msg.edit(content=f"❌ Fehler: {e}")

@bot.tree.command(name="zen-security-check", description="🔍 Prüft aktuelle Server-Sicherheit")
@app_commands.checks.has_permissions(administrator=True)
async def security_check(interaction: discord.Interaction):
    """Prüft die aktuellen Sicherheitseinstellungen des Servers"""
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    
    # Prüfe @everyone
    everyone = guild.default_role
    everyone_perms = everyone.permissions
    
    issues = []
    status = []
    
    # Kritische Berechtigungen für @everyone
    if everyone_perms.administrator:
        issues.append("🚨 @everyone hat Administrator-Rechte!")
    if everyone_perms.manage_guild:
        issues.append("🚨 @everyone kann den Server verwalten!")
    if everyone_perms.manage_roles:
        issues.append("🚨 @everyone kann Rollen verwalten!")
    if everyone_perms.manage_channels:
        issues.append("🚨 @everyone kann Kanäle verwalten!")
    if everyone_perms.kick_members:
        issues.append("⚠️ @everyone kann Mitglieder kicken!")
    if everyone_perms.ban_members:
        issues.append("⚠️ @everyone kann Mitglieder bannen!")
    
    # Sichtbarkeit
    if everyone_perms.read_messages:
        issues.append("⚠️ @everyone kann alle Kanäle sehen (ohne Beitritt)")
    
    # Prüfe Member-Rolle
    member_role = discord.utils.get(guild.roles, name="Member")
    if member_role:
        status.append("✅ Member-Rolle existiert")
        member_perms = member_role.permissions
        
        if member_perms.manage_guild:
            issues.append("⚠️ Member-Rolle kann Server verwalten!")
        if member_perms.manage_roles:
            issues.append("⚠️ Member-Rolle kann Rollen verwalten!")
    else:
        issues.append("❌ Keine Member-Rolle gefunden!")
    
    # Erstelle Embed
    if issues:
        embed = discord.Embed(
            title="🔍 Sicherheits-Check: PROBLEME GEFUNDEN",
            color=ERROR_COLOR
        )
        embed.description = "\n".join(issues)
        embed.add_field(
            name="Status",
            value="\n".join(status) if status else "Keine Status-Infos",
            inline=False
        )
        embed.set_footer(text="Führe /zen-security-setup aus um Probleme zu beheben")
    else:
        embed = discord.Embed(
            title="🔍 Sicherheits-Check: ALLES OK",
            description="✅ Der Server ist korrekt konfiguriert!",
            color=SUCCESS_COLOR
        )
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="zen-add-member", description="➕ Weist einem Benutzer die Member-Rolle zu")
@app_commands.checks.has_permissions(manage_roles=True)
async def add_member(
    interaction: discord.Interaction,
    user: discord.Member
):
    """Weist einem Benutzer die Member-Rolle zu"""
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    member_role = discord.utils.get(guild.roles, name="Member")
    
    if not member_role:
        await interaction.followup.send(
            "❌ Member-Rolle nicht gefunden! Führe zuerst /zen-security-setup aus.",
            ephemeral=True
        )
        return
    
    if member_role in user.roles:
        await interaction.followup.send(
            f"ℹ️ {user.mention} hat bereits die Member-Rolle.",
            ephemeral=True
        )
        return
    
    try:
        await user.add_roles(member_role, reason=f"Durch {interaction.user}")
        await interaction.followup.send(
            f"✅ {user.mention} wurde die Member-Rolle zugewiesen!",
            ephemeral=True
        )
    except discord.Forbidden:
        await interaction.followup.send(
            "❌ Keine Berechtigung! Bot-Rolle muss über Member-Rolle sein.",
            ephemeral=True
        )

@bot.event
async def on_member_join(member):
    """Automatisch Member-Rolle zuweisen bei Server-Beitritt"""
    if member.bot:
        return
    
    member_role = discord.utils.get(member.guild.roles, name="Member")
    if member_role:
        try:
            await member.add_roles(member_role, reason="Automatisch bei Beitritt")
            print(f"✅ Member-Rolle an {member} vergeben")
        except:
            pass

@security_setup.error
@security_check.error
async def admin_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ Du brauchst Administrator-Rechte für diesen Befehl!",
            ephemeral=True
        )

@add_member.error
async def mod_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ Du brauchst Rollen-Verwaltungs-Rechte für diesen Befehl!",
            ephemeral=True
        )

def main():
    """Hauptfunktion"""
    token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not token:
        print("❌ DISCORD_BOT_TOKEN nicht gefunden!")
        print("Setze die Umgebungsvariable:")
        print("  export DISCORD_BOT_TOKEN='dein_token'")
        return
    
    print("🚀 Starte Discord Security Bot...")
    print("Befehle:")
    print("  /zen-security-setup - Server sicher konfigurieren")
    print("  /zen-security-check  - Sicherheit prüfen")
    print("  /zen-add-member      - Member-Rolle zuweisen")
    
    bot.run(token)

if __name__ == "__main__":
    main()

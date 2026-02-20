#!/usr/bin/env python3
"""
Screenshot Manager für Zen-Ai Pentest Web UI
Kopiert Screenshots in das Projekt-Verzeichnis
"""

import argparse
import shutil
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def get_screenshot_dir():
    """Erstelle und gib Screenshot-Verzeichnis zurück"""
    screenshot_dir = Path.home() / "Zen-Ai-Pentest" / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    return screenshot_dir


def list_screenshots():
    """Liste alle Screenshots auf"""
    screenshot_dir = get_screenshot_dir()

    screenshots = []
    for ext in ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp"]:
        screenshots.extend(screenshot_dir.glob(ext))

    if not screenshots:
        console.print("[yellow]⚠️  Keine Screenshots gefunden[/yellow]")
        console.print(f"[dim]Verzeichnis: {screenshot_dir}[/dim]")
        return []

    table = Table(title=f"📸 Screenshots ({len(screenshots)})")
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Name", style="green")
    table.add_column("Größe", style="yellow")
    table.add_column("Datum", style="blue")

    for i, screenshot in enumerate(sorted(screenshots, key=lambda x: x.stat().st_mtime, reverse=True), 1):
        stat = screenshot.stat()
        size = f"{stat.st_size / 1024:.1f} KB"
        date = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        table.add_row(str(i), screenshot.name, size, date)

    console.print(table)
    return screenshots


def add_screenshot(source_path, rename=None):
    """Füge Screenshot hinzu"""
    source = Path(source_path).expanduser()

    if not source.exists():
        console.print(f"[red]❌ Datei nicht gefunden: {source}[/red]")
        return False

    screenshot_dir = get_screenshot_dir()

    # Generiere Dateinamen
    if rename:
        filename = rename
        if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
            filename += source.suffix
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{source.name}"

    destination = screenshot_dir / filename

    try:
        shutil.copy2(source, destination)
        console.print(
            Panel(
                f"[green]✅ Screenshot hinzugefügt![/green]\n\n"
                f"Datei: {filename}\n"
                f"Pfad: {destination}\n"
                f"URL: http://127.0.0.1:5000/static/screenshots/{filename}",
                title="Screenshot",
                border_style="green",
            )
        )
        return True
    except Exception as e:
        console.print(f"[red]❌ Fehler beim Kopieren: {e}[/red]")
        return False


def add_from_downloads():
    """Suche und füge Screenshots aus Downloads hinzu"""
    downloads_dir = Path.home() / "Downloads"

    if not downloads_dir.exists():
        console.print("[red]❌ Downloads-Verzeichnis nicht gefunden[/red]")
        return

    # Suche nach Screenshots
    screenshots = []
    for pattern in ["Screenshot*.png", "Screenshot*.jpg", "*zen*.png", "*kimi*.png", "*pentest*.png"]:
        screenshots.extend(downloads_dir.glob(pattern))

    if not screenshots:
        console.print("[yellow]⚠️  Keine Screenshots in Downloads gefunden[/yellow]")
        console.print("[dim]Suche nach: Screenshot*.png, *zen*.png, *kimi*.png[/dim]")
        return

    console.print(f"[green]📸 {len(screenshots)} Screenshot(s) in Downloads gefunden:[/green]")

    for screenshot in screenshots:
        console.print(f"  • {screenshot.name}")

    console.print()
    response = input("Alle Screenshots kopieren? (j/n): ").lower()

    if response == "j":
        success_count = 0
        for screenshot in screenshots:
            if add_screenshot(screenshot):
                success_count += 1

        console.print(f"\n[green]✅ {success_count}/{len(screenshots)} Screenshots kopiert[/green]")
        console.print("[blue]🌐 Web UI: http://127.0.0.1:5000 → Tab 'Screenshots'[/blue]")


def delete_screenshot(filename):
    """Lösche Screenshot"""
    screenshot_dir = get_screenshot_dir()
    filepath = screenshot_dir / filename

    if not filepath.exists():
        console.print(f"[red]❌ Screenshot nicht gefunden: {filename}[/red]")
        return False

    try:
        filepath.unlink()
        console.print(f"[green]✅ Gelöscht: {filename}[/green]")
        return True
    except Exception as e:
        console.print(f"[red]❌ Fehler: {e}[/red]")
        return False


def open_screenshot_dir():
    """Öffne Screenshot-Verzeichnis im Dateimanager"""
    screenshot_dir = get_screenshot_dir()

    # Versuche verschiedene Dateimanager
    commands = [
        ["xdg-open", str(screenshot_dir)],  # Linux
        ["explorer", str(screenshot_dir)],  # Windows
        ["open", str(screenshot_dir)],  # macOS
    ]

    for cmd in commands:
        try:
            import subprocess

            subprocess.run(cmd, check=True)
            console.print(f"[green]📂 Geöffnet: {screenshot_dir}[/green]")
            return
        except Exception:
            continue

    console.print("[yellow]⚠️  Konnte Dateimanager nicht öffnen[/yellow]")
    console.print(f"[dim]Pfad: {screenshot_dir}[/dim]")


def main():
    parser = argparse.ArgumentParser(
        description="Screenshot Manager für Zen-Ai Pentest",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s list                          # Liste alle Screenshots
  %(prog)s add ~/Downloads/screenshot.png # Screenshot hinzufügen
  %(prog)s add ~/Downloads/img.png -n recon # Mit Namen hinzufügen
  %(prog)s downloads                     # Aus Downloads suchen
  %(prog)s open                          # Verzeichnis öffnen
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Befehle")

    # List
    subparsers.add_parser("list", help="Liste alle Screenshots")

    # Add
    p_add = subparsers.add_parser("add", help="Screenshot hinzufügen")
    p_add.add_argument("path", help="Pfad zum Screenshot")
    p_add.add_argument("-n", "--name", help="Neuer Dateiname (optional)")

    # Downloads
    subparsers.add_parser("downloads", help="Screenshots aus Downloads suchen")

    # Delete
    p_del = subparsers.add_parser("delete", help="Screenshot löschen")
    p_del.add_argument("filename", help="Dateiname des Screenshots")

    # Open
    subparsers.add_parser("open", help="Screenshot-Verzeichnis öffnen")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "list":
        list_screenshots()
    elif args.command == "add":
        add_screenshot(args.path, args.name)
    elif args.command == "downloads":
        add_from_downloads()
    elif args.command == "delete":
        delete_screenshot(args.filename)
    elif args.command == "open":
        open_screenshot_dir()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Repository Status Card Generator
Erstellt eine visuelle Status-Karte mit Overlay und QR-Code
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

def install_package(package):
    """Installiert fehlende Packages"""
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])

# Dependencies prüfen/installieren
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Installiere Pillow...")
    install_package("Pillow")
    from PIL import Image, ImageDraw, ImageFont

try:
    import qrcode
except ImportError:
    print("Installiere qrcode...")
    install_package("qrcode[pil]")
    import qrcode

# Pfade
BASE_DIR = Path(__file__).parent.parent
ASSETS_DIR = BASE_DIR / "assets"
DOCS_DIR = BASE_DIR / "docs"
OUTPUT_DIR = BASE_DIR / "docs" / "status"

def get_repo_stats():
    """Sammelt aktuelle Repository-Statistiken"""
    stats = {
        "version": "2.3.9",
        "date": datetime.now().strftime("%d.%m.%Y"),
        "workflows": 56,
        "tests": 97,
        "docs": 60,
        "telegram": "ON",
        "discord": "ON",
        "iso27001": "85%",
        "security": "2 alerts",
        "last_update": "13.02.2026"
    }
    
    # Versuche git stats zu bekommen
    try:
        result = subprocess.run(
            ["git", "-C", str(BASE_DIR), "log", "--oneline", "-1"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            stats["last_commit"] = result.stdout.strip()[:50]
    except:
        stats["last_commit"] = "N/A"
    
    return stats

def create_qr_code(url, size=150):
    """Erstellt QR-Code"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="white", back_color="#0d1117")
    return img.resize((size, size))

def generate_status_card():
    """Generiert die Status-Karte"""
    
    print("Generiere Repository Status Card...")
    
    # Stats sammeln
    stats = get_repo_stats()
    
    # Basis-Bild laden (oder neues erstellen)
    base_image_path = ASSETS_DIR / "kimi_ai_base.png"
    
    if base_image_path.exists():
        img = Image.open(base_image_path).convert("RGBA")
    else:
        # Fallback: Neues Bild mit Kimi-Farben
        img = Image.new("RGBA", (800, 1000), "#0d1117")
    
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # Farben
    bg_color = (13, 17, 23, 230)  # Semi-transparent dark
    text_color = (255, 255, 255)
    accent_color = (88, 166, 255)  # GitHub blue
    green_color = (35, 197, 94)    # Success green
    yellow_color = (210, 153, 34)  # Warning yellow
    
    # Overlay-Bereich erstellen (untere Hälfte)
    overlay_height = 400
    overlay = Image.new("RGBA", (width, overlay_height), bg_color)
    img.paste(overlay, (0, height - overlay_height), overlay)
    
    # Titel
    try:
        title_font = ImageFont.truetype("arial.ttf", 32)
        header_font = ImageFont.truetype("arial.ttf", 24)
        text_font = ImageFont.truetype("arial.ttf", 18)
        small_font = ImageFont.truetype("arial.ttf", 14)
    except:
        title_font = ImageFont.load_default()
        header_font = text_font = small_font = title_font
    
    # Titel zeichnen
    title = "Zen-AI-Pentest Status"
    draw.text((width//2 - 180, height - overlay_height + 20), 
              title, fill=text_color, font=title_font)
    
    # Version & Datum
    draw.text((30, height - overlay_height + 70), 
              f"Version: {stats['version']}  |  {stats['date']}", 
              fill=accent_color, font=text_font)
    
    # Status-Boxen
    box_y = height - overlay_height + 110
    box_height = 50
    box_width = 230
    
    # Box 1: Integrations
    draw.rounded_rectangle([30, box_y, 30 + box_width, box_y + box_height], 
                          radius=10, fill=(22, 27, 34), outline=accent_color, width=2)
    draw.text((40, box_y + 5), "Integrations", fill=text_color, font=header_font)
    draw.text((40, box_y + 28), f"Telegram {stats['telegram']} | Discord {stats['discord']}", 
              fill=green_color, font=text_font)
    
    # Box 2: Compliance
    draw.rounded_rectangle([30 + box_width + 20, box_y, 30 + box_width*2 + 20, box_y + box_height], 
                          radius=10, fill=(22, 27, 34), outline=accent_color, width=2)
    draw.text((40 + box_width + 20, box_y + 5), "Compliance", fill=text_color, font=header_font)
    draw.text((40 + box_width + 20, box_y + 28), f"ISO 27001: {stats['iso27001']}", 
              fill=yellow_color, font=text_font)
    
    # Box 3: Stats
    draw.rounded_rectangle([30, box_y + box_height + 20, 30 + box_width*2 + 20, box_y + box_height*2 + 20], 
                          radius=10, fill=(22, 27, 34), outline=accent_color, width=2)
    draw.text((40, box_y + box_height + 25), "Repository Stats", fill=text_color, font=header_font)
    stats_text = f"Workflows: {stats['workflows']}  |  Tests: {stats['tests']}  |  Docs: {stats['docs']}"
    draw.text((40, box_y + box_height + 48), stats_text, fill=text_color, font=text_font)
    
    # Security Status
    sec_y = box_y + box_height*2 + 40
    draw.text((30, sec_y), f"Security: {stats['security']}", fill=yellow_color, font=text_font)
    draw.text((30, sec_y + 25), f"Last Update: {stats['last_update']}", fill=(139, 148, 158), font=small_font)
    
    # QR-Code hinzufügen
    qr_url = "https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/PROJECT_STATUS_COMPLETE.md"
    qr_img = create_qr_code(qr_url, 120)
    
    # QR-Code Position (rechts unten)
    qr_x = width - 150
    qr_y = height - 150
    img.paste(qr_img, (qr_x, qr_y), qr_img if qr_img.mode == 'RGBA' else None)
    
    # QR-Code Label
    draw.text((qr_x - 20, qr_y + 125), "Scan for Details", fill=text_color, font=small_font)
    
    # Speichern
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "repo_status_card.png"
    img.save(output_path, "PNG")
    
    print(f"Status Card gespeichert: {output_path}")
    print(f"Stats: {stats['workflows']} Workflows, {stats['tests']} Tests, ISO {stats['iso27001']}")
    
    return output_path

def update_readme_with_card():
    """Aktualisiert README.md mit der Status-Karte"""
    readme_path = BASE_DIR / "README.md"
    
    if not readme_path.exists():
        print("⚠️  README.md nicht gefunden")
        return
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Prüfe ob bereits Status-Karte eingebunden
    card_markdown = "\n![Repository Status](docs/status/repo_status_card.png)\n"
    
    if "repo_status_card.png" not in content:
        # Füge nach dem ersten Header ein
        lines = content.split('\n')
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('# ') and insert_idx == 0:
                insert_idx = i + 1
        
        lines.insert(insert_idx, card_markdown)
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print("README.md aktualisiert mit Status-Karte")
    else:
        print("Status-Karte bereits in README.md vorhanden")

if __name__ == "__main__":
    print("=" * 60)
    print("Zen-AI-Pentest Repository Status Card Generator")
    print("=" * 60)
    
    # Status-Karte generieren
    output_file = generate_status_card()
    
    # README aktualisieren
    update_readme_with_card()
    
    print("\nFertig!")
    print(f"Output: {output_file}")
    print("\nTipp: Führe dieses Script aus nach wichtigen Änderungen:")
    print("   python scripts/generate_repo_status_card.py")

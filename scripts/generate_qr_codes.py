#!/usr/bin/env python3
"""
QR Code Generator für Zen-AI-Pentest
Erstellt QR-Codes für alle wichtigen Links
"""

import qrcode
import os
from PIL import Image, ImageDraw, ImageFont

def create_qr_with_label(url, label, filename, output_dir="qr_codes"):
    """Erstellt einen QR-Code mit Beschriftung"""
    
    # Output-Verzeichnis erstellen
    os.makedirs(output_dir, exist_ok=True)
    
    # QR-Code generieren
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # QR-Code als Bild (konvertiere zu RGB für Kompatibilität)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    # Größe anpassen
    qr_width, qr_height = qr_img.size
    
    # Neues Bild mit Platz für Text
    label_height = 80
    total_height = qr_height + label_height
    
    final_img = Image.new('RGB', (qr_width, total_height), 'white')
    final_img.paste(qr_img, (0, 0))
    
    # Text hinzufügen
    draw = ImageDraw.Draw(final_img)
    
    # Schriftart (versuche verschiedene)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except:
            font = ImageFont.load_default()
    
    # Label zentrieren
    bbox = draw.textbbox((0, 0), label, font=font)
    text_width = bbox[2] - bbox[0]
    x = (qr_width - text_width) // 2
    y = qr_height + 20
    
    draw.text((x, y), label, fill="black", font=font)
    
    # URL kleiner darunter
    url_short = url[:50] + "..." if len(url) > 50 else url
    try:
        small_font = ImageFont.truetype("arial.ttf", 12)
    except:
        small_font = font
    
    bbox_url = draw.textbbox((0, 0), url_short, font=small_font)
    url_width = bbox_url[2] - bbox_url[0]
    x_url = (qr_width - url_width) // 2
    y_url = y + 30
    
    draw.text((x_url, y_url), url_short, fill="gray", font=small_font)
    
    # Speichern
    filepath = os.path.join(output_dir, filename)
    final_img.save(filepath)
    print(f"[OK] {filepath}")
    return filepath


def main():
    print("=" * 70)
    print(">> QR Code Generator fuer Zen-AI-Pentest")
    print("=" * 70)
    print()
    
    output_dir = "docs/qr_codes"
    os.makedirs(output_dir, exist_ok=True)
    
    # Links mit Labels
    links = [
        {
            "url": "https://github.com/SHAdd0WTAka/Zen-Ai-Pentest",
            "label": "GitHub Repository",
            "filename": "01_github_repo.png"
        },
        {
            "url": "https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/actions",
            "label": "GitHub Actions",
            "filename": "02_github_actions.png"
        },
        {
            "url": "https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/settings/environments",
            "label": "GitHub Environments",
            "filename": "03_github_env.png"
        },
        {
            "url": "https://discord.gg/BSmCqjhY",
            "label": "Discord Server",
            "filename": "04_discord.png"
        },
        {
            "url": "https://t.me/botfather",
            "label": "Telegram BotFather",
            "filename": "05_telegram_botfather.png"
        },
        {
            "url": "https://pypi.org/project/zen-ai-pentest/",
            "label": "PyPI Package",
            "filename": "06_pypi.png"
        },
        {
            "url": "https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/docs/TELEGRAM_SETUP.md",
            "label": "Telegram Setup Guide",
            "filename": "07_telegram_guide.png"
        },
        {
            "url": "https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/docs/DISCORD_SETUP.md",
            "label": "Discord Setup Guide",
            "filename": "08_discord_guide.png"
        },
    ]
    
    print("[INFO] Generiere QR-Codes...")
    print()
    
    generated_files = []
    for link in links:
        filepath = create_qr_with_label(
            link["url"], 
            link["label"], 
            link["filename"],
            output_dir
        )
        generated_files.append((link["label"], filepath))
    
    print()
    print("=" * 70)
    print("[OK] Alle QR-Codes erstellt!")
    print("=" * 70)
    print()
    print(f"[INFO] Gespeichert in: {output_dir}/")
    print()
    print("QR-Codes:")
    for label, filepath in generated_files:
        print(f"  • {label}")
        print(f"    -> {filepath}")
    print()
    print("[TIP] Scanne den QR-Code mit deinem Handy!")
    print()


if __name__ == "__main__":
    main()

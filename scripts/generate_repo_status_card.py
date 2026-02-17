#!/usr/bin/env python3
"""
Repository Status Card Generator - Optimized Layout
"""

import sys
import subprocess
from datetime import datetime
from pathlib import Path

def install_package(package):
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Installing Pillow...")
    install_package("Pillow")
    from PIL import Image, ImageDraw, ImageFont

try:
    import qrcode
except ImportError:
    print("Installing qrcode...")
    install_package("qrcode[pil]")
    import qrcode

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "docs" / "status"

def get_repo_stats():
    stats = {
        "version": "2.3.9",
        "date": datetime.now().strftime("%d.%m.%Y"),
        "workflows": "56",
        "tests": "97",
        "docs": "60+",
        "telegram": "ON",
        "discord": "ON",
        "iso27001": "85%",
        "security": "2 alerts",
    }
    try:
        result = subprocess.run(
            ["git", "-C", str(BASE_DIR), "log", "--oneline", "-1"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            stats["last_commit"] = result.stdout.strip()[:40]
    except Exception:
        stats["last_commit"] = "N/A"
    return stats

def create_qr_code(url, size=100):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="white", back_color="#0d1117")
    return img.resize((size, size))

def generate_status_card():
    print("Generating Repository Status Card...")

    stats = get_repo_stats()

    # Kompakte Größe: 700x400 (statt 800x1000)
    width, height = 700, 400
    img = Image.new("RGBA", (width, height), "#0d1117")
    draw = ImageDraw.Draw(img)

    # Farben
    text_color = (255, 255, 255)
    accent_color = (88, 166, 255)
    green_color = (35, 197, 94)
    yellow_color = (210, 153, 34)
    gray_color = (139, 148, 158)

    # Fonts
    try:
        title_font = ImageFont.truetype("arial.ttf", 28)
        header_font = ImageFont.truetype("arial.ttf", 16)
        text_font = ImageFont.truetype("arial.ttf", 14)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except Exception:
        title_font = ImageFont.load_default()
        header_font = text_font = small_font = title_font

    # Hintergrund-Gradient (subtil)
    for y in range(height):
        draw.line([(0, y), (width, y)], fill=(13, 17, 23, 255))

    # Header-Bereich
    draw.text((30, 20), "Zen-AI-Pentest", fill=text_color, font=title_font)
    draw.text((30, 55), f"v{stats['version']} | {stats['date']}", fill=accent_color, font=text_font)

    # Linie unter Header
    draw.line([(30, 80), (width-30, 80)], fill=(48, 54, 61), width=1)

    # 3 Boxen in einer Reihe
    box_y = 100
    box_height = 70
    box_width = 200

    # Box 1: Integrations
    x1 = 30
    draw.rounded_rectangle([x1, box_y, x1 + box_width, box_y + box_height],
                          radius=8, fill=(22, 27, 34), outline=accent_color, width=2)
    draw.text((x1 + 10, box_y + 8), "Integrations", fill=text_color, font=header_font)
    draw.text((x1 + 10, box_y + 32), f"Telegram: {stats['telegram']}", fill=green_color, font=text_font)
    draw.text((x1 + 10, box_y + 48), f"Discord: {stats['discord']}", fill=green_color, font=text_font)

    # Box 2: Compliance
    x2 = x1 + box_width + 15
    draw.rounded_rectangle([x2, box_y, x2 + box_width, box_y + box_height],
                          radius=8, fill=(22, 27, 34), outline=accent_color, width=2)
    draw.text((x2 + 10, box_y + 8), "Compliance", fill=text_color, font=header_font)
    draw.text((x2 + 10, box_y + 35), f"ISO 27001: {stats['iso27001']}", fill=yellow_color, font=text_font)

    # Box 3: Stats
    x3 = x2 + box_width + 15
    draw.rounded_rectangle([x3, box_y, x3 + box_width, box_y + box_height],
                          radius=8, fill=(22, 27, 34), outline=accent_color, width=2)
    draw.text((x3 + 10, box_y + 8), "Repository", fill=text_color, font=header_font)
    draw.text((x3 + 10, box_y + 28), f"Workflows: {stats['workflows']}", fill=gray_color, font=text_font)
    draw.text((x3 + 10, box_y + 44), f"Tests: {stats['tests']}", fill=gray_color, font=text_font)

    # Unterer Bereich
    bottom_y = 200

    # Security Status
    draw.text((30, bottom_y), f"Security: {stats['security']}", fill=yellow_color, font=text_font)
    draw.text((30, bottom_y + 20), f"Last Update: {stats['date']}", fill=gray_color, font=small_font)

    # QR Code (rechts unten) - Link to AGENTS.md for AI Agents
    qr_url = "https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/AGENTS.md"
    qr_img = create_qr_code(qr_url, 90)
    qr_x = width - 120
    qr_y = height - 120
    img.paste(qr_img, (qr_x, qr_y), qr_img if qr_img.mode == 'RGBA' else None)
    draw.text((qr_x - 10, qr_y + 95), "Scan for Details", fill=gray_color, font=small_font)

    # Speichern
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "repo_status_card.png"
    img.save(output_path, "PNG")

    print(f"Status Card saved: {output_path}")
    print(f"Size: {width}x{height} (optimized)")
    return output_path

def update_readme_with_card():
    readme_path = BASE_DIR / "README.md"

    if not readme_path.exists():
        print("README.md not found")
        return

    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    card_markdown = "![Repository Status](docs/status/repo_status_card.png)\n\n"

    if "repo_status_card.png" not in content:
        lines = content.split('\n')
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('# ') and insert_idx == 0:
                insert_idx = i + 1

        lines.insert(insert_idx, card_markdown)

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print("README.md updated")
    else:
        print("README.md already has status card")

if __name__ == "__main__":
    print("=" * 50)
    print("Zen-AI-Pentest Status Card Generator")
    print("=" * 50)

    output_file = generate_status_card()
    update_readme_with_card()

    print("\nDone!")
    print(f"Output: {output_file}")

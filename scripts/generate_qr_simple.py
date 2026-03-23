#!/usr/bin/env python3
"""
Simple QR Code Generator - Compatible format
"""

import os

import qrcode


def create_qr(url, filename, output_dir="docs/qr_codes"):
    """Erstellt einen einfachen QR-Code"""
    os.makedirs(output_dir, exist_ok=True)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Erstelle Bild
    img = qr.make_image(fill_color="black", back_color="white")

    # Konvertiere zu RGB
    img = img.convert("RGB")

    # Speichern
    filepath = os.path.join(output_dir, filename)
    img.save(filepath, "PNG")
    print(f"[OK] {filepath}")
    return filepath


def main():
    print("=" * 60)
    print("QR Code Generator")
    print("=" * 60)

    links = [
        ("https://discord.gg/zJZUJwK9AC", "discord_qr.png"),
        ("https://t.me/botfather", "telegram_botfather_qr.png"),
        (
            "https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/settings/environments",
            "github_env_qr.png",
        ),
        (
            "https://github.com/SHAdd0WTAka/Zen-Ai-Pentest",
            "github_repo_qr.png",
        ),
        (
            "https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/actions",
            "github_actions_qr.png",
        ),
    ]

    for url, filename in links:
        create_qr(url, filename)

    print("=" * 60)
    print("Fertig!")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Multilingual Wordlist Generator for Zen-AI-Pentest
Generates targeted wordlists for different languages and contexts
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set


@dataclass
class LanguageProfile:
    """Language-specific word patterns"""

    code: str
    name: str
    common_words: List[str]
    common_numbers: List[str]
    keyboard_patterns: List[str]
    date_formats: List[str]
    special_suffixes: List[str]


LANGUAGE_PROFILES = {
    "en": LanguageProfile(
        code="en",
        name="English",
        common_words=[
            "password",
            "welcome",
            "admin",
            "user",
            "login",
            "master",
            "dragon",
            "monkey",
            "shadow",
            "sunshine",
            "princess",
            "football",
            "baseball",
            "iloveyou",
            "trustno1",
            "abc123",
            "letmein",
            "whatever",
            "starwars",
        ],
        common_numbers=[
            "123",
            "1234",
            "12345",
            "123456",
            "1234567",
            "12345678",
            "123456789",
            "007",
            "666",
            "777",
            "888",
            "999",
            "000",
            "111",
            "321",
            "654",
        ],
        keyboard_patterns=[
            "qwerty",
            "qwertz",
            "asdf",
            "zxcv",
            "qazwsx",
            "1q2w3e",
            "1qaz2wsx",
            "qweasd",
            "wasd",
        ],
        date_formats=["2024", "2025", "2026", "1990", "2000", "2010", "2020"],
        special_suffixes=["!", "@", "#", "123", "1", "01", "2024", "!!!"],
    ),
    "de": LanguageProfile(
        code="de",
        name="German",
        common_words=[
            "passwort",
            "hallo",
            "liebe",
            "schatz",
            "mama",
            "papa",
            "hund",
            "katze",
            "berlin",
            "münchen",
            "hamburg",
            "köln",
            "deutschland",
            "schloss",
            "engel",
            "musik",
            "fussball",
            "auto",
            "arbeit",
            "sonne",
        ],
        common_numbers=[
            "123",
            "1234",
            "12345",
            "123456",
            "4711",
            "1989",
            "1990",
            "1963",
            "007",
            "666",
            "888",
            "1234567890",
        ],
        keyboard_patterns=["qwertz", "asdfgh", "yxcvbn", "123qwe", "qaywsx"],
        date_formats=["2024", "2025", "2026", "1989", "1990", "2000", "2010"],
        special_suffixes=[
            "!",
            "123",
            "1",
            "01",
            "2024",
            "!!",
            "?",
            ".",
            "_",
            "_1",
        ],
    ),
    "es": LanguageProfile(
        code="es",
        name="Spanish",
        common_words=[
            "contraseña",
            "amor",
            "vida",
            "casa",
            "perro",
            "gato",
            "madrid",
            "barcelona",
            "españa",
            "hola",
            "secreto",
            "cielo",
            "angel",
            "princesa",
            "rey",
            "corazon",
            "familia",
            "chocolate",
        ],
        common_numbers=[
            "123",
            "1234",
            "12345",
            "123456",
            "007",
            "666",
            "777",
            "000",
            "1989",
            "1990",
            "1995",
            "2000",
        ],
        keyboard_patterns=["qwerty", "asdf", "zxcv", "123qwe"],
        date_formats=["2024", "2025", "2026", "1990", "2000", "2010"],
        special_suffixes=["!", "123", "1", "_", ".", "2024", "!!"],
    ),
    "fr": LanguageProfile(
        code="fr",
        name="French",
        common_words=[
            "motdepasse",
            "amour",
            "bonjour",
            "france",
            "paris",
            "soleil",
            "chéri",
            "chérie",
            "fleur",
            "chat",
            "chien",
            "princesse",
            "ange",
            "maison",
            "bonheur",
            "coeur",
            "etoile",
            "liberte",
        ],
        common_numbers=[
            "123",
            "1234",
            "12345",
            "123456",
            "007",
            "666",
            "999",
            "1989",
            "1990",
            "1995",
            "2000",
            "1789",
        ],
        keyboard_patterns=["azerty", "qsdfgh", "wxcvbn", "123aze"],
        date_formats=["2024", "2025", "2026", "1990", "2000", "2010"],
        special_suffixes=["!", "123", "1", "_", "-", "2024", "!!", "?"],
    ),
    "it": LanguageProfile(
        code="it",
        name="Italian",
        common_words=[
            "password",
            "amore",
            "ciao",
            "roma",
            "milano",
            "italia",
            "sole",
            "cuore",
            "angelo",
            "vita",
            "casa",
            "famiglia",
            "calcio",
            "napoli",
            "juventus",
            "mamma",
            "papa",
        ],
        common_numbers=[
            "123",
            "1234",
            "12345",
            "123456",
            "007",
            "666",
            "777",
            "1990",
            "2000",
            "2010",
            "1899",
        ],
        keyboard_patterns=["qwerty", "asdf", "zxcv"],
        date_formats=["2024", "2025", "2026", "1990", "2000", "2010"],
        special_suffixes=["!", "123", "1", "_", "2024", "!!"],
    ),
    "ru": LanguageProfile(
        code="ru",
        name="Russian",
        common_words=[
            "пароль",
            "любовь",
            "солнце",
            "мама",
            "папа",
            "москва",
            "россия",
            "друг",
            "кошка",
            "собака",
            "жизнь",
            "счастье",
            "мир",
            "дом",
        ],
        common_numbers=[
            "123",
            "1234",
            "12345",
            "007",
            "666",
            "999",
            "1989",
            "2000",
        ],
        keyboard_patterns=["йцукен", "фывапр", "ячсмить", "12345"],
        date_formats=["2024", "2025", "2026", "1990", "2000"],
        special_suffixes=["!", "123", "1", "_", "2024"],
    ),
    "zh": LanguageProfile(
        code="zh",
        name="Chinese",
        common_words=[
            "密码",
            "123456",
            "123456789",
            "qwerty",
            "我爱你",
            "和谐",
            "自由",
            "中国",
            "北京",
            "上海",
            "深圳",
            "广州",
            " dragon",
            "monkey",
        ],
        common_numbers=[
            "123",
            "1234",
            "12345",
            "123456",
            "123456789",
            "520",
            "1314",
            "666",
            "888",
            "999",
            "2008",
            "2024",
        ],
        keyboard_patterns=["qwerty", "asdf", "zxcv", "1qaz"],
        date_formats=["2024", "2025", "2026", "2008", "2010", "2020"],
        special_suffixes=["123", "1", "!", "520", "1314", "888"],
    ),
}


class WordlistGenerator:
    """Generate targeted wordlists for pentesting"""

    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path(__file__).parent

    def generate_mutations(self, base_words: List[str], numbers: List[str], suffixes: List[str]) -> Set[str]:
        """Generate password mutations"""
        passwords = set()

        for word in base_words:
            # Lowercase
            passwords.add(word.lower())
            # Capitalize
            passwords.add(word.capitalize())
            # Uppercase
            passwords.add(word.upper())

            # With numbers
            for num in numbers:
                passwords.add(f"{word}{num}")
                passwords.add(f"{word.lower()}{num}")
                passwords.add(f"{word.capitalize()}{num}")
                passwords.add(f"{num}{word}")

            # With suffixes
            for suffix in suffixes:
                passwords.add(f"{word}{suffix}")
                passwords.add(f"{word.lower()}{suffix}")
                passwords.add(f"{word.capitalize()}{suffix}")

        return passwords

    def generate_keyboard_combinations(self, patterns: List[str]) -> Set[str]:
        """Generate keyboard pattern combinations"""
        combos = set()

        for pattern in patterns:
            # Direct
            combos.add(pattern)
            # Reversed
            combos.add(pattern[::-1])
            # With numbers
            for i in range(10):
                combos.add(f"{pattern}{i}")
                combos.add(f"{pattern}{i}{i}")
            # Capitalized variations
            combos.add(pattern.upper())
            combos.add(pattern.capitalize())

        return combos

    def generate_for_language(self, lang_code: str, max_size: int = 10000) -> List[str]:
        """Generate wordlist for specific language"""
        if lang_code not in LANGUAGE_PROFILES:
            raise ValueError(f"Unknown language code: {lang_code}")

        profile = LANGUAGE_PROFILES[lang_code]
        passwords = set()

        print(f"🔤 Generating wordlist for {profile.name}...")

        # 1. Common words with mutations
        word_mutations = self.generate_mutations(
            profile.common_words,
            profile.common_numbers,
            profile.special_suffixes,
        )
        passwords.update(word_mutations)

        # 2. Keyboard patterns
        keyboard_combos = self.generate_keyboard_combinations(profile.keyboard_patterns)
        passwords.update(keyboard_combos)

        # 3. Date-based passwords
        for year in profile.date_formats:
            passwords.add(year)
            for word in profile.common_words[:5]:
                passwords.add(f"{word}{year}")
                passwords.add(f"{word}{year[-2:]}")  # Last 2 digits

        # 4. Leet speak variations (basic)
        leet_map = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"}
        for word in list(passwords)[:500]:  # Limit leet mutations
            leet_word = word
            for char, replacement in leet_map.items():
                leet_word = leet_word.replace(char, replacement)
            if leet_word != word:
                passwords.add(leet_word)

        # Sort and limit
        sorted_passwords = sorted(passwords, key=lambda x: (len(x), x))
        final_list = sorted_passwords[:max_size]

        print(f"   Generated: {len(final_list)} passwords")
        return final_list

    def save_wordlist(self, lang_code: str, passwords: List[str]):
        """Save wordlist to file"""
        output_dir = self.base_path / "custom" / lang_code
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "generated.txt"

        profile = LANGUAGE_PROFILES.get(lang_code)
        lang_name = profile.name if profile else lang_code

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# Zen-AI-Pentest Generated Wordlist\n")
            f.write(f"# Language: {lang_name}\n")
            f.write(f"# Count: {len(passwords)}\n")
            f.write(f"# Generated: {__import__('datetime').datetime.now().isoformat()}\n")
            f.write("#\n")
            for pwd in passwords:
                f.write(f"{pwd}\n")

        print(f"   💾 Saved: {output_file}")
        return output_file

    def generate_all(self):
        """Generate wordlists for all supported languages"""
        print("=" * 60)
        print("🌍 Generating Multilingual Wordlists")
        print("=" * 60)

        results = {}
        for lang_code in LANGUAGE_PROFILES:
            passwords = self.generate_for_language(lang_code)
            output_file = self.save_wordlist(lang_code, passwords)
            results[lang_code] = {
                "count": len(passwords),
                "file": str(output_file),
            }

        # Save manifest
        manifest_file = self.base_path / "custom" / "manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        print("\n" + "=" * 60)
        print("✅ All wordlists generated!")
        print("=" * 60)
        total = sum(r["count"] for r in results.values())
        print(f"Total passwords: {total:,}")
        for lang, info in results.items():
            print(f"  {lang}: {info['count']:,} passwords")

        return results


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Multilingual Wordlist Generator")
    parser.add_argument("--all", action="store_true", help="Generate all languages")
    parser.add_argument(
        "--lang",
        type=str,
        help="Generate specific language (en,de,es,fr,it,ru,zh)",
    )
    parser.add_argument("--size", type=int, default=10000, help="Max passwords per language")

    args = parser.parse_args()

    generator = WordlistGenerator()

    if args.all:
        generator.generate_all()
    elif args.lang:
        passwords = generator.generate_for_language(args.lang, args.size)
        generator.save_wordlist(args.lang, passwords)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

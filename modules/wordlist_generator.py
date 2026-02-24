"""
Wordlist Generator Module

Generates targeted wordlists for penetration testing:
- Company-specific wordlists
- Target-based permutations
- Pattern-based generation
- Leaked password mutations

Author: SHAdd0WTAka + Kimi AI
"""

import itertools
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class WordlistConfig:
    """Configuration for wordlist generation"""

    min_length: int = 4
    max_length: int = 20
    include_numbers: bool = True
    include_special: bool = False
    include_years: bool = True
    years_range: List[int] = field(
        default_factory=lambda: [2020, 2021, 2022, 2023, 2024, 2025]
    )
    mutations: bool = True
    mutation_level: str = "medium"  # low, medium, high


class WordlistGenerator:
    """
    Generate targeted wordlists for password attacks.

    Features:
    - Target-specific word generation
    - Pattern-based permutations
    - Common password mutations
    - Seasonal/year-based passwords
    """

    COMMON_SUFFIXES = [
        "1",
        "12",
        "123",
        "1234",
        "12345",
        "01",
        "02",
        "03",
        "04",
        "05",
        "06",
        "07",
        "08",
        "09",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "20",
        "00",
        "99",
        "88",
        "77",
        "66",
        "55",
        "44",
        "33",
        "22",
        "11",
        "007",
        "666",
        "777",
        "888",
        "999",
        "000",
        "!",
        "!!",
        "@",
        "#",
        "$",
        "%",
        "&",
        "*",
        "2023",
        "2024",
        "2025",
        "23",
        "24",
        "25",
    ]

    COMMON_PREFIXES = [
        "",
        "The",
        "My",
        "Mr",
        "Ms",
        "Dr",
        "Admin",
        "User",
        "Test",
    ]

    SPECIAL_CHARS = ["!", "@", "#", "$", "%", "&", "*", "?", "_", "-"]

    SEASONS = ["Spring", "Summer", "Fall", "Autumn", "Winter"]
    MONTHS = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    LEET_SPEAK = {
        "a": ["4", "@"],
        "e": ["3"],
        "i": ["1", "!"],
        "o": ["0"],
        "s": ["5", "$"],
        "t": ["7"],
        "l": ["1"],
        "g": ["9"],
        "b": ["8"],
    }

    def __init__(self, config: Optional[WordlistConfig] = None):
        self.config = config or WordlistConfig()
        self.generated_words: Set[str] = set()

    def generate_company_wordlist(
        self,
        company_name: str,
        industry: Optional[str] = None,
        locations: Optional[List[str]] = None,
        extras: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Generate wordlist based on company information.

        Args:
            company_name: Company name
            industry: Industry type (tech, finance, etc.)
            locations: Office locations
            extras: Additional keywords
        """
        words = set()

        # Base words
        base_words = self._extract_base_words(company_name)
        words.update(base_words)

        # Add industry terms
        if industry:
            industry_words = self._get_industry_words(industry)
            words.update(industry_words)

        # Add locations
        if locations:
            words.update(locations)

        # Add extras
        if extras:
            words.update(extras)

        # Generate permutations
        all_words = set(words)
        for word in words:
            all_words.update(self._generate_permutations(word))
            all_words.update(self._add_numbers(word))
            all_words.update(self._add_special(word))

            if self.config.mutations:
                all_words.update(self._mutate_word(word))

        # Add years
        if self.config.include_years:
            for word in list(all_words)[:50]:  # Limit to prevent explosion
                for year in self.config.years_range:
                    all_words.add(f"{word}{year}")
                    all_words.add(f"{year}{word}")

        # Filter by length
        filtered = {
            w
            for w in all_words
            if self.config.min_length <= len(w) <= self.config.max_length
        }

        return sorted(list(filtered))

    def generate_targeted_wordlist(
        self, target_info: Dict[str, Any]
    ) -> List[str]:
        """
        Generate wordlist from target information.

        target_info can include:
        - first_name, last_name
        - birthdate
        - pet_names
        - hobbies
        - favorite_things
        """
        # Extract all information
        keywords = []

        if "first_name" in target_info:
            keywords.append(target_info["first_name"])
            keywords.append(target_info["first_name"].lower())
            keywords.append(target_info["first_name"].capitalize())

        if "last_name" in target_info:
            keywords.append(target_info["last_name"])
            keywords.append(target_info["last_name"].lower())
            keywords.append(target_info["last_name"].capitalize())

        if "birthdate" in target_info:
            bd = target_info["birthdate"]
            # Various date formats
            keywords.extend(
                [
                    bd.replace("-", ""),
                    bd.replace("-", "")[2:],
                    bd.split("-")[0],  # year
                    bd.split("-")[1],  # month
                    bd.split("-")[2],  # day
                ]
            )

        if "pet_names" in target_info:
            keywords.extend(target_info["pet_names"])

        if "hobbies" in target_info:
            keywords.extend(target_info["hobbies"])

        if "favorite_things" in target_info:
            keywords.extend(target_info["favorite_things"])

        # Generate combinations
        base_words = set(keywords)

        # Add combinations of first + last name
        if "first_name" in target_info and "last_name" in target_info:
            first = target_info["first_name"]
            last = target_info["last_name"]
            combinations = [
                f"{first}{last}",
                f"{first}.{last}",
                f"{first}_{last}",
                f"{first[0]}{last}",
                f"{first}{last[0]}",
                f"{last}{first}",
                f"{first[0]}.{last}",
                f"{first}{last[0]}",
            ]
            base_words.update(combinations)

        # Generate permutations for all words
        all_words = set(base_words)
        for word in base_words:
            all_words.update(self._generate_permutations(word))
            all_words.update(self._add_numbers(word))

            if self.config.mutations:
                all_words.update(self._mutate_word(word))

        return sorted(list(all_words))

    def generate_pattern_wordlist(
        self, pattern: str, values: Dict[str, List[str]]
    ) -> List[str]:
        """
        Generate wordlist from pattern.

        Pattern example: "{word}{number}{special}"
        Values: {"word": ["Pass", "Secret"], "number": ["1", "2"], "special": ["!", "@"]}
        """
        import re

        # Find all placeholders
        placeholders = re.findall(r"\{(\w+)\}", pattern)

        # Get value lists for each placeholder
        value_lists = []
        for ph in placeholders:
            if ph in values:
                value_lists.append(values[ph])
            else:
                value_lists.append([f"{{{ph}}}"])

        # Generate all combinations
        words = set()
        for combo in itertools.product(*value_lists):
            word = pattern
            for ph, val in zip(placeholders, combo):
                word = word.replace(f"{{{ph}}}", val, 1)
            words.add(word)

        return sorted(list(words))

    def mutate_password(self, base_password: str) -> List[str]:
        """
        Generate common password mutations.

        Mutations include:
        - Case variations
        - Leet speak
        - Appending numbers/special chars
        - Common substitutions
        """
        mutations = set()
        mutations.add(base_password)

        # Case variations
        mutations.add(base_password.lower())
        mutations.add(base_password.upper())
        mutations.add(base_password.capitalize())
        mutations.add(base_password.swapcase())

        # Leet speak
        leet_versions = self._apply_leet_speak(base_password)
        mutations.update(leet_versions)

        # Add numbers
        mutations.update(self._add_numbers(base_password))

        # Add special chars
        if self.config.include_special:
            mutations.update(self._add_special(base_password))

        # Reverse
        mutations.add(base_password[::-1])

        # Duplicate
        mutations.add(base_password * 2)
        mutations.add(base_password * 3)

        # Common substitutions
        subs = [
            ("a", "@"),
            ("a", "4"),
            ("e", "3"),
            ("i", "1"),
            ("i", "!"),
            ("o", "0"),
            ("s", "$"),
            ("s", "5"),
            ("t", "7"),
        ]

        for old, new in subs:
            mutated = base_password.replace(old, new).replace(old.upper(), new)
            mutations.add(mutated)
            mutations.add(mutated.capitalize())

        return sorted(list(mutations))

    def generate_common_passwords(self, count: int = 10000) -> List[str]:
        """Generate list of common passwords with variations"""
        common_bases = [
            "password",
            "123456",
            "12345678",
            "qwerty",
            "abc123",
            "monkey",
            "letmein",
            "dragon",
            "111111",
            "baseball",
            "iloveyou",
            "trustno1",
            "sunshine",
            "princess",
            "admin",
            "welcome",
            "shadow",
            "ashley",
            "football",
            "jesus",
            "michael",
            "ninja",
            "mustang",
            "password1",
            "123456789",
            "adobe123",
            "admin123",
            "root",
            "toor",
            "guest",
            "default",
            "changeme",
            "p@ssw0rd",
            "Passw0rd",
            "Password1",
        ]

        passwords = set(common_bases)

        # Add mutations
        for base in common_bases[:50]:  # Top 50
            passwords.update(self.mutate_password(base))

        # Add years
        for base in common_bases[:20]:
            for year in self.config.years_range:
                passwords.add(f"{base}{year}")
                passwords.add(f"{base}{str(year)[2:]}")

        return sorted(list(passwords))[:count]

    def save_wordlist(self, words: List[str], filepath: str):
        """Save wordlist to file"""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            for word in words:
                f.write(f"{word}\n")

        return path.absolute()

    def _extract_base_words(self, text: str) -> Set[str]:
        """Extract base words from company name"""
        words = set()

        # Original
        words.add(text)
        words.add(text.lower())
        words.add(text.upper())
        words.add(text.capitalize())

        # Remove spaces
        words.add(text.replace(" ", ""))
        words.add(text.replace(" ", "").lower())

        # Remove special chars
        clean = "".join(c for c in text if c.isalnum())
        words.add(clean)
        words.add(clean.lower())

        # Acronyms
        if " " in text:
            acronym = "".join(word[0] for word in text.split() if word)
            words.add(acronym)
            words.add(acronym.upper())
            words.add(acronym.lower())

        return words

    def _get_industry_words(self, industry: str) -> Set[str]:
        """Get common words for industry"""
        industry_terms = {
            "tech": [
                "tech",
                "software",
                "digital",
                "data",
                "cloud",
                "cyber",
                "it",
            ],
            "finance": [
                "finance",
                "bank",
                "money",
                "capital",
                "invest",
                "trade",
            ],
            "healthcare": ["health", "medical", "care", "clinic", "patient"],
            "education": ["edu", "school", "learn", "student", "academy"],
            "retail": ["shop", "store", "retail", "sale", "market"],
        }

        return set(industry_terms.get(industry.lower(), []))

    def _generate_permutations(self, word: str) -> Set[str]:
        """Generate case and format permutations"""
        perms = {
            word,
            word.lower(),
            word.upper(),
            word.capitalize(),
            word.swapcase(),
        }

        # CamelCase
        if " " in word:
            camel = "".join(w.capitalize() for w in word.split())
            perms.add(camel)
            perms.add(camel.lower())

        return perms

    def _add_numbers(self, word: str) -> Set[str]:
        """Add number suffixes/prefixes"""
        results = set()

        for suffix in self.COMMON_SUFFIXES:
            results.add(f"{word}{suffix}")
            results.add(f"{suffix}{word}")

        return results

    def _add_special(self, word: str) -> Set[str]:
        """Add special characters"""
        results = set()

        for char in self.SPECIAL_CHARS:
            results.add(f"{word}{char}")
            results.add(f"{char}{word}")
            results.add(f"{word}{char}{char}")

        return results

    def _mutate_word(self, word: str) -> Set[str]:
        """Apply word mutations"""
        mutations = set()

        # Add years
        for year in self.config.years_range:
            mutations.add(f"{word}{year}")
            mutations.add(f"{word}{str(year)[2:]}")

        # Add seasons
        for season in self.SEASONS:
            mutations.add(f"{word}{season}")
            mutations.add(f"{season}{word}")

        # Add months
        for month in self.MONTHS:
            mutations.add(f"{word}{month}")
            mutations.add(f"{month}{word}")

        return mutations

    def _apply_leet_speak(self, text: str) -> Set[str]:
        """Apply leet speak transformations"""
        results = set()

        # Simple replacements
        for char, replacements in self.LEET_SPEAK.items():
            for replacement in replacements:
                leet = text.replace(char, replacement).replace(
                    char.upper(), replacement
                )
                results.add(leet)

        return results


# Convenience functions
def generate_company_wordlist(company: str, **kwargs) -> List[str]:
    """Quick company wordlist generation"""
    gen = WordlistGenerator()
    return gen.generate_company_wordlist(company, **kwargs)


def generate_password_mutations(password: str) -> List[str]:
    """Quick password mutation"""
    gen = WordlistGenerator()
    return gen.mutate_password(password)


def generate_target_wordlist(info: Dict[str, Any]) -> List[str]:
    """Quick targeted wordlist"""
    gen = WordlistGenerator()
    return gen.generate_targeted_wordlist(info)

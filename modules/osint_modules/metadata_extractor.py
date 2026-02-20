#!/usr/bin/env python3
"""
Metadata-Extractor Modul für Zen-Ai-Pentest
===========================================
Extrahiert Metadaten aus verschiedenen Dateitypen:
- PDF-Dokumente
- Microsoft Office
- Bilder (EXIF)
- HTML/Meta-Tags
- Archive
- Ausführbare Dateien

Autor: ResearchBot-Team
Version: 1.0.0
Lizenz: MIT (Ethical Use Only)
"""

import asyncio
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger("ZenAI.OSINT.Metadata")


@dataclass
class Metadata:
    """Metadaten-Datenklasse"""

    source: str
    file_type: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    created: Optional[str] = None
    modified: Optional[str] = None
    software: Optional[str] = None
    version: Optional[str] = None
    comments: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    pages: Optional[int] = None
    language: Optional[str] = None
    raw: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


class MetadataExtractor:
    """
    Metadata-Extractor für OSINT

    Extrahiert versteckte Informationen aus Dateien.
    """

    # Unterstützte Dateitypen
    SUPPORTED_TYPES = {
        "pdf": [".pdf"],
        "office": [".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"],
        "image": [".jpg", ".jpeg", ".png", ".gif", ".tiff", ".bmp"],
        "archive": [".zip", ".tar", ".gz", ".bz2", ".7z", ".rar"],
        "executable": [".exe", ".dll", ".so", ".dylib"],
        "web": [".html", ".htm", ".css", ".js"],
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialisiert den Metadata-Extractor

        Args:
            config: Optionale Konfiguration
        """
        self.config = config or {}
        self.timeout = self.config.get("timeout", 30.0)
        self.extract_raw = self.config.get("extract_raw", True)

        logger.info("MetadataExtractor initialisiert")

    async def extract_from_url(self, url: str) -> Optional[Metadata]:
        """
        Extrahiert Metadaten von einer URL

        Args:
            url: Ziel-URL

        Returns:
            Metadata-Objekt oder None
        """
        logger.info(f"Extrahiere Metadaten von: {url}")

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout, ssl=False) as response:
                    if response.status == 200:
                        content_type = response.headers.get("Content-Type", "")
                        content = await response.read()

                        # Bestimme Dateityp
                        file_type = self._detect_file_type(url, content_type, content)

                        # Extrahiere Metadaten
                        return await self._extract_metadata(content, file_type, url)

        except ImportError:
            logger.debug("aiohttp nicht verfügbar")
        except Exception as e:
            logger.debug(f"Fehler beim Extrahieren: {e}")

        return None

    async def extract_from_file(self, filepath: str) -> Optional[Metadata]:
        """
        Extrahiert Metadaten aus einer Datei

        Args:
            filepath: Pfad zur Datei

        Returns:
            Metadata-Objekt oder None
        """
        logger.info(f"Extrahiere Metadaten aus: {filepath}")

        try:
            with open(filepath, "rb") as f:
                content = f.read()

            # Bestimme Dateityp
            file_type = self._detect_file_type(filepath, None, content)

            # Extrahiere Metadaten
            return await self._extract_metadata(content, file_type, filepath)

        except Exception as e:
            logger.debug(f"Fehler beim Lesen der Datei: {e}")

        return None

    async def extract_from_html(self, html: str, url: str) -> Metadata:
        """
        Extrahiert Metadaten aus HTML

        Args:
            html: HTML-Inhalt
            url: Quell-URL

        Returns:
            Metadata-Objekt
        """
        metadata = Metadata(source=url, file_type="html")

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")

            # Titel
            title_tag = soup.find("title")
            if title_tag:
                metadata.title = title_tag.get_text(strip=True)

            # Meta-Tags
            for meta in soup.find_all("meta"):
                name = meta.get("name", meta.get("property", "")).lower()
                content = meta.get("content", "")

                if name in ["author", "article:author"]:
                    metadata.author = content
                elif name in ["description", "og:description"]:
                    metadata.comments = content
                elif name == "keywords":
                    metadata.keywords = [k.strip() for k in content.split(",")]
                elif name == "generator":
                    metadata.software = content
                elif name in ["created", "article:published_time"]:
                    metadata.created = content
                elif name in ["modified", "article:modified_time"]:
                    metadata.modified = content

            # Open Graph
            og_title = soup.find("meta", property="og:title")
            if og_title and not metadata.title:
                metadata.title = og_title.get("content", "")

            # Sprache
            html_tag = soup.find("html")
            if html_tag:
                metadata.language = html_tag.get("lang", "")

        except ImportError:
            # Fallback zu Regex
            title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
            if title_match:
                metadata.title = title_match.group(1).strip()

            author_match = re.search(r'<meta[^>]*name=["\']?author["\']?[^>]*content=["\']?([^"\']+)', html, re.IGNORECASE)
            if author_match:
                metadata.author = author_match.group(1)

        return metadata

    def _detect_file_type(self, source: str, content_type: Optional[str], content: bytes) -> str:
        """Erkennt den Dateityp"""
        source_lower = source.lower()

        # Prüfe Dateiendung
        for file_type, extensions in self.SUPPORTED_TYPES.items():
            for ext in extensions:
                if source_lower.endswith(ext):
                    return file_type

        # Prüfe Content-Type
        if content_type:
            if "pdf" in content_type:
                return "pdf"
            elif "image" in content_type:
                return "image"
            elif "html" in content_type:
                return "web"
            elif "zip" in content_type or "archive" in content_type:
                return "archive"

        # Prüfe Magic Bytes
        if content:
            if content[:4] == b"%PDF":
                return "pdf"
            elif content[:2] == b"\xff\xd8":
                return "image"
            elif content[:4] == b"\x89PNG":
                return "image"
            elif content[:4] == b"GIF8":
                return "image"
            elif content[:2] == b"PK":
                return "archive"
            elif content[:4] == b"<!DO" or content[:4] == b"<htm":
                return "web"

        return "unknown"

    async def _extract_metadata(self, content: bytes, file_type: str, source: str) -> Optional[Metadata]:
        """Extrahiert Metadaten basierend auf Dateityp"""
        if file_type == "pdf":
            return await self._extract_pdf_metadata(content, source)
        elif file_type == "office":
            return await self._extract_office_metadata(content, source)
        elif file_type == "image":
            return await self._extract_image_metadata(content, source)
        elif file_type == "archive":
            return await self._extract_archive_metadata(content, source)
        elif file_type == "web":
            return await self.extract_from_html(content.decode("utf-8", errors="ignore"), source)

        return None

    async def _extract_pdf_metadata(self, content: bytes, source: str) -> Optional[Metadata]:
        """Extrahiert PDF-Metadaten"""
        metadata = Metadata(source=source, file_type="pdf")

        try:
            import io

            from PyPDF2 import PdfReader

            reader = PdfReader(io.BytesIO(content))

            if reader.metadata:
                meta = reader.metadata

                metadata.title = meta.get("/Title", "")
                metadata.author = meta.get("/Author", "")
                metadata.creator = meta.get("/Creator", "")
                metadata.producer = meta.get("/Producer", "")

                if meta.get("/CreationDate"):
                    metadata.created = str(meta.get("/CreationDate"))
                if meta.get("/ModDate"):
                    metadata.modified = str(meta.get("/ModDate"))

                metadata.pages = len(reader.pages)

                if self.extract_raw:
                    metadata.raw = {k: str(v) for k, v in meta.items()}

            return metadata

        except ImportError:
            logger.debug("PyPDF2 nicht verfügbar")
        except Exception as e:
            logger.debug(f"PDF-Extraktion fehlgeschlagen: {e}")

        # Fallback: Regex-basierte Extraktion
        try:
            text = content.decode("latin-1", errors="ignore")

            # Suche nach Metadaten
            patterns = {
                "title": r"/Title\s*\(([^)]+)\)",
                "author": r"/Author\s*\(([^)]+)\)",
                "creator": r"/Creator\s*\(([^)]+)\)",
                "producer": r"/Producer\s*\(([^)]+)\)",
            }

            for field, pattern in patterns.items():
                match = re.search(pattern, text)
                if match:
                    setattr(metadata, field, match.group(1))

            return metadata

        except Exception as e:
            logger.debug(f"Fallback PDF-Extraktion fehlgeschlagen: {e}")

        return None

    async def _extract_office_metadata(self, content: bytes, source: str) -> Optional[Metadata]:
        """Extrahiert Office-Dokument-Metadaten"""
        metadata = Metadata(source=source, file_type="office")

        try:
            import io

            from docx import Document

            doc = Document(io.BytesIO(content))

            # Core-Eigenschaften
            if doc.core_properties:
                props = doc.core_properties

                metadata.title = props.title
                metadata.author = props.author
                metadata.created = props.created.isoformat() if props.created else None
                metadata.modified = props.modified.isoformat() if props.modified else None
                metadata.comments = props.comments
                metadata.keywords = props.keywords.split(",") if props.keywords else []

                if self.extract_raw:
                    metadata.raw = {
                        "category": props.category,
                        "content_status": props.content_status,
                        "identifier": props.identifier,
                        "language": props.language,
                        "subject": props.subject,
                        "version": props.version,
                    }

            return metadata

        except ImportError:
            logger.debug("python-docx nicht verfügbar")
        except Exception as e:
            logger.debug(f"Office-Extraktion fehlgeschlagen: {e}")

        return None

    async def _extract_image_metadata(self, content: bytes, source: str) -> Optional[Metadata]:
        """Extrahiert Bild-Metadaten (EXIF)"""
        metadata = Metadata(source=source, file_type="image")

        try:
            import io

            from PIL import Image
            from PIL.ExifTags import GPSTAGS, TAGS

            img = Image.open(io.BytesIO(content))

            # EXIF-Daten
            if hasattr(img, "_getexif") and img._getexif():
                exifdata = img._getexif()

                for tag_id, value in exifdata.items():
                    tag = TAGS.get(tag_id, tag_id)

                    if tag == "Make":
                        metadata.software = str(value)
                    elif tag == "Model":
                        metadata.software = f"{metadata.software or ''} {value}".strip()
                    elif tag == "DateTime":
                        metadata.created = str(value)
                    elif tag == "DateTimeOriginal":
                        metadata.created = str(value)
                    elif tag == "Artist":
                        metadata.author = str(value)
                    elif tag == "Copyright":
                        metadata.comments = str(value)
                    elif tag == "ImageDescription":
                        metadata.title = str(value)

                if self.extract_raw:
                    metadata.raw = {TAGS.get(k, k): str(v) for k, v in exifdata.items()}

            # Bildgröße
            metadata.raw["width"] = img.width
            metadata.raw["height"] = img.height
            metadata.raw["format"] = img.format
            metadata.raw["mode"] = img.mode

            return metadata

        except ImportError:
            logger.debug("PIL nicht verfügbar")
        except Exception as e:
            logger.debug(f"Bild-Extraktion fehlgeschlagen: {e}")

        return None

    async def _extract_archive_metadata(self, content: bytes, source: str) -> Optional[Metadata]:
        """Extrahiert Archiv-Metadaten"""
        metadata = Metadata(source=source, file_type="archive")

        try:
            import io
            import zipfile

            with zipfile.ZipFile(io.BytesIO(content), "r") as zf:
                metadata.comments = zf.comment.decode("utf-8", errors="ignore") if zf.comment else None

                file_list = []
                for info in zf.infolist():
                    file_list.append(
                        {
                            "name": info.filename,
                            "size": info.file_size,
                            "compressed": info.compress_size,
                            "date": datetime(*info.date_time).isoformat() if info.date_time else None,
                        }
                    )

                metadata.raw["files"] = file_list
                metadata.raw["file_count"] = len(file_list)

            return metadata

        except ImportError:
            logger.debug("zipfile nicht verfügbar")
        except Exception as e:
            logger.debug(f"Archiv-Extraktion fehlgeschlagen: {e}")

        return None

    def get_sensitive_info(self, metadata: Metadata) -> List[str]:
        """Identifiziert potenziell sensible Informationen"""
        sensitive = []

        # Prüfe auf Benutzernamen in Software-Feldern
        if metadata.software:
            if "username" in metadata.software.lower() or "user" in metadata.software.lower():
                sensitive.append(f"Software: {metadata.software}")

        # Prüfe auf Netzwerk-Pfade
        for field_value in [metadata.raw.get("Template", ""), metadata.raw.get("Company", "")]:
            if isinstance(field_value, str) and "\\\\" in field_value:
                sensitive.append(f"Netzwerk-Pfad: {field_value}")

        # Prüfe auf E-Mail-Adressen
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        for key, value in metadata.raw.items():
            if isinstance(value, str):
                emails = re.findall(email_pattern, value)
                if emails:
                    sensitive.append(f"E-Mail in {key}: {emails}")

        return sensitive


async def main():
    """CLI-Interface für Metadata-Extractor"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Metadata Extractor")
    parser.add_argument("source", help="URL oder Dateipfad")
    parser.add_argument("--file", action="store_true", help="Quelle ist Datei")
    parser.add_argument("-o", "--output", help="Ausgabedatei")
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    extractor = MetadataExtractor()

    if args.file:
        result = await extractor.extract_from_file(args.source)
    else:
        result = await extractor.extract_from_url(args.source)

    if result:
        # Ausgabe
        print(json.dumps(result.to_dict(), indent=2))

        # Sensible Informationen
        sensitive = extractor.get_sensitive_info(result)
        if sensitive:
            print("\n=== Potenziell sensible Informationen ===")
            for item in sensitive:
                print(f"  - {item}")
    else:
        print("Keine Metadaten gefunden")

    if args.output and result:
        with open(args.output, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"\nErgebnisse gespeichert in: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())

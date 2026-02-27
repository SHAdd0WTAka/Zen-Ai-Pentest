"""
Evidence Storage Management

Handles storage of evidence files with support for:
- Local filesystem
- MinIO/S3 compatible object storage
- Encryption at rest
- Retention policies
"""

import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


class EvidenceStorage:
    """
    Manages storage of evidence files.
    
    Default: Local filesystem
    Optional: S3/MinIO for distributed setups
    """
    
    def __init__(
        self,
        base_path: str = "evidence",
        use_s3: bool = False,
        s3_endpoint: Optional[str] = None,
        s3_bucket: Optional[str] = None,
        encryption_key: Optional[str] = None,
    ):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories
        self.screenshots_dir = self.base_path / "screenshots"
        self.logs_dir = self.base_path / "logs"
        self.exports_dir = self.base_path / "exports"
        self.temp_dir = self.base_path / "temp"
        
        for d in [self.screenshots_dir, self.logs_dir, self.exports_dir, self.temp_dir]:
            d.mkdir(exist_ok=True)
        
        # S3 settings (optional)
        self.use_s3 = use_s3
        self.s3_endpoint = s3_endpoint
        self.s3_bucket = s3_bucket
        self.encryption_key = encryption_key
        
        if use_s3:
            self._init_s3()
    
    def _init_s3(self):
        """Initialize S3/MinIO client."""
        try:
            import boto3
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=self.s3_endpoint,
                aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
                aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
            )
        except ImportError:
            raise ImportError("boto3 required for S3 storage. Install with: pip install boto3")
    
    def save_screenshot(self, evidence_id: str, source_path: str) -> str:
        """
        Save screenshot to storage.
        
        Args:
            evidence_id: Evidence UUID
            source_path: Path to source file
            
        Returns:
            Storage path
        """
        dest_path = self.screenshots_dir / f"{evidence_id}.png"
        shutil.copy2(source_path, dest_path)
        
        if self.use_s3:
            self._upload_to_s3(str(dest_path), f"screenshots/{evidence_id}.png")
        
        return str(dest_path)
    
    def save_json(self, evidence_id: str, data: dict) -> str:
        """
        Save JSON data to storage.
        
        Args:
            evidence_id: Evidence UUID
            data: JSON-serializable data
            
        Returns:
            Storage path
        """
        dest_path = self.logs_dir / f"{evidence_id}.json"
        with open(dest_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        
        if self.use_s3:
            self._upload_to_s3(str(dest_path), f"logs/{evidence_id}.json")
        
        return str(dest_path)
    
    def save_text(self, evidence_id: str, content: str) -> str:
        """
        Save text content to storage.
        
        Args:
            evidence_id: Evidence UUID
            content: Text content
            
        Returns:
            Storage path
        """
        dest_path = self.logs_dir / f"{evidence_id}.txt"
        with open(dest_path, "w") as f:
            f.write(content)
        
        if self.use_s3:
            self._upload_to_s3(str(dest_path), f"logs/{evidence_id}.txt")
        
        return str(dest_path)
    
    def save_binary(self, evidence_id: str, data: bytes, extension: str = "bin") -> str:
        """
        Save binary data to storage.
        
        Args:
            evidence_id: Evidence UUID
            data: Binary data
            extension: File extension
            
        Returns:
            Storage path
        """
        dest_path = self.logs_dir / f"{evidence_id}.{extension}"
        with open(dest_path, "wb") as f:
            f.write(data)
        
        if self.use_s3:
            self._upload_to_s3(str(dest_path), f"logs/{evidence_id}.{extension}")
        
        return str(dest_path)
    
    def get_file(self, evidence_id: str, file_type: str = "screenshot") -> Optional[bytes]:
        """
        Retrieve file from storage.
        
        Args:
            evidence_id: Evidence UUID
            file_type: Type of file (screenshot, log, export)
            
        Returns:
            File contents as bytes
        """
        if file_type == "screenshot":
            path = self.screenshots_dir / f"{evidence_id}.png"
        elif file_type == "log":
            # Try JSON first, then TXT
            path = self.logs_dir / f"{evidence_id}.json"
            if not path.exists():
                path = self.logs_dir / f"{evidence_id}.txt"
        else:
            path = self.logs_dir / f"{evidence_id}.{file_type}"
        
        if path.exists():
            with open(path, "rb") as f:
                return f.read()
        
        # Try S3 if local not found
        if self.use_s3:
            return self._download_from_s3(f"{file_type}s/{evidence_id}.png")
        
        return None
    
    def delete_file(self, evidence_id: str, file_type: str = "screenshot") -> bool:
        """
        Delete file from storage.
        
        Args:
            evidence_id: Evidence UUID
            file_type: Type of file
            
        Returns:
            True if deleted, False if not found
        """
        deleted = False
        
        # Delete from local
        if file_type == "screenshot":
            path = self.screenshots_dir / f"{evidence_id}.png"
        else:
            path = self.logs_dir / f"{evidence_id}.{file_type}"
        
        if path.exists():
            path.unlink()
            deleted = True
        
        # Delete from S3
        if self.use_s3:
            self._delete_from_s3(f"{file_type}s/{evidence_id}.png")
            deleted = True
        
        return deleted
    
    def _upload_to_s3(self, local_path: str, s3_key: str):
        """Upload file to S3/MinIO."""
        if not self.use_s3:
            return
        
        extra_args = {}
        if self.encryption_key:
            extra_args["SSECustomerKey"] = self.encryption_key
            extra_args["SSECustomerAlgorithm"] = "AES256"
        
        self.s3_client.upload_file(local_path, self.s3_bucket, s3_key, ExtraArgs=extra_args)
    
    def _download_from_s3(self, s3_key: str) -> Optional[bytes]:
        """Download file from S3/MinIO."""
        if not self.use_s3:
            return None
        
        try:
            import io
            buffer = io.BytesIO()
            self.s3_client.download_fileobj(self.s3_bucket, s3_key, buffer)
            return buffer.getvalue()
        except Exception:
            return None
    
    def _delete_from_s3(self, s3_key: str):
        """Delete file from S3/MinIO."""
        if not self.use_s3:
            return
        
        try:
            self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_key)
        except Exception:
            pass
    
    def cleanup_old_files(self, days: int = 90) -> Dict:
        """
        Clean up files older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Cleanup statistics
        """
        cutoff = datetime.now() - timedelta(days=days)
        stats = {"deleted": 0, "errors": 0, "bytes_freed": 0}
        
        for directory in [self.screenshots_dir, self.logs_dir]:
            for file_path in directory.iterdir():
                try:
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff:
                        size = file_path.stat().st_size
                        file_path.unlink()
                        stats["deleted"] += 1
                        stats["bytes_freed"] += size
                except Exception:
                    stats["errors"] += 1
        
        return stats
    
    def get_storage_stats(self) -> Dict:
        """
        Get storage usage statistics.
        
        Returns:
            Storage statistics
        """
        def dir_stats(path: Path) -> Dict:
            total_size = 0
            file_count = 0
            for f in path.iterdir():
                if f.is_file():
                    total_size += f.stat().st_size
                    file_count += 1
            return {"size_bytes": total_size, "file_count": file_count}
        
        return {
            "screenshots": dir_stats(self.screenshots_dir),
            "logs": dir_stats(self.logs_dir),
            "exports": dir_stats(self.exports_dir),
            "total": {
                "size_bytes": (
                    dir_stats(self.screenshots_dir)["size_bytes"] +
                    dir_stats(self.logs_dir)["size_bytes"] +
                    dir_stats(self.exports_dir)["size_bytes"]
                ),
                "file_count": (
                    dir_stats(self.screenshots_dir)["file_count"] +
                    dir_stats(self.logs_dir)["file_count"] +
                    dir_stats(self.exports_dir)["file_count"]
                ),
            },
        }


class EvidenceExporter:
    """
    Export evidence for legal proceedings.
    """
    
    def __init__(self, storage: EvidenceStorage):
        self.storage = storage
    
    def export_to_pdf(self, evidence_list: List[Dict], output_path: str) -> str:
        """
        Export evidence to PDF report.
        
        Args:
            evidence_list: List of evidence dictionaries
            output_path: Output file path
            
        Returns:
            Path to generated PDF
        """
        try:
            from weasyprint import HTML
            
            html_content = self._generate_html_report(evidence_list)
            HTML(string=html_content).write_pdf(output_path)
            
            return output_path
        except ImportError:
            raise ImportError("weasyprint required for PDF export. Install with: pip install weasyprint")
    
    def export_to_html(self, evidence_list: List[Dict], output_path: str) -> str:
        """
        Export evidence to HTML report.
        
        Args:
            evidence_list: List of evidence dictionaries
            output_path: Output file path
            
        Returns:
            Path to generated HTML
        """
        html_content = self._generate_html_report(evidence_list)
        
        with open(output_path, "w") as f:
            f.write(html_content)
        
        return output_path
    
    def export_to_json(self, evidence_list: List[Dict], output_path: str) -> str:
        """
        Export evidence to JSON.
        
        Args:
            evidence_list: List of evidence dictionaries
            output_path: Output file path
            
        Returns:
            Path to generated JSON
        """
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "evidence_count": len(evidence_list),
            "evidence": evidence_list,
        }
        
        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return output_path
    
    def _generate_html_report(self, evidence_list: List[Dict]) -> str:
        """Generate HTML report from evidence."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Evidence Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { border-bottom: 2px solid #333; margin-bottom: 30px; }
                .evidence { margin-bottom: 40px; border: 1px solid #ddd; padding: 20px; }
                .severity-critical { border-left: 5px solid #dc3545; }
                .severity-high { border-left: 5px solid #fd7e14; }
                .severity-medium { border-left: 5px solid #ffc107; }
                .severity-low { border-left: 5px solid #28a745; }
                .metadata { color: #666; font-size: 0.9em; }
                .proof { background: #f8f9fa; padding: 15px; border-radius: 5px; }
                img { max-width: 100%; border: 1px solid #ddd; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Penetration Test Evidence Report</h1>
                <p>Generated: """ + datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC") + """</p>
                <p>Total Evidence: """ + str(len(evidence_list)) + """</p>
            </div>
        """
        
        for evidence in evidence_list:
            severity = evidence.get("severity", "info")
            html += f"""
            <div class="evidence severity-{severity}">
                <h2>{evidence.get("title", "Untitled")}</h2>
                <div class="metadata">
                    <p><strong>ID:</strong> {evidence.get("id")}</p>
                    <p><strong>Severity:</strong> {severity.upper()}</p>
                    <p><strong>Type:</strong> {evidence.get("vulnerability_type")}</p>
                    <p><strong>Target:</strong> {evidence.get("target", {}).get("url", "N/A")}</p>
                    <p><strong>Collected:</strong> {evidence.get("timestamps", {}).get("collected")}</p>
                </div>
                <p>{evidence.get("description", "")}</p>
                {f'<div class="proof"><pre>{evidence.get("proof_of_concept")}</pre></div>' if evidence.get("proof_of_concept") else ""}
                {f'<img src="file://{evidence.get("file", {}).get("path")}" alt="Screenshot"/>' if evidence.get("file", {}).get("path") else ""}
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html

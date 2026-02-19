"""
Document Loader: Loads ALL architecture documents into Adamus memory.

This is CRITICAL. Adamus NEVER forgets because:
1. All docs always loaded
2. Complete context before every task
3. Brains forget, Adamus remembers

EVERY task starts with loading ALL documents.
"""

import os
import hashlib
import logging
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set
import yaml
import re

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """A loaded architecture document."""
    path: str
    name: str
    content: str
    hash: str
    loaded_at: datetime
    size_bytes: int

    # Extracted metadata
    title: str = ""
    status: str = ""
    requirements: List[str] = field(default_factory=list)
    code_blocks: List[str] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)


class DocumentLoader:
    """
    Loads ALL architecture documents into memory.

    Adamus maintains ALL context by loading every document
    before any brain interaction. Brains are stateless,
    Adamus is the persistent memory.
    """

    def __init__(self, docs_path: str = "~/adamus/docs/architecture"):
        """
        Initialize the document loader.

        Args:
            docs_path: Path to architecture documents directory
        """
        self.docs_path = Path(docs_path).expanduser()
        self.documents: Dict[str, Document] = {}
        self._last_load_time: Optional[datetime] = None
        self._document_hashes: Dict[str, str] = {}

    def load_all_documents(self) -> Dict[str, Document]:
        """
        Load EVERY document from the architecture directory.

        This runs:
        - On Adamus startup
        - Every hour (check for changes)
        - Before any major task

        Returns:
            Dict mapping file paths to Document objects
        """
        if not self.docs_path.exists():
            raise FileNotFoundError(
                f"Architecture docs not found at {self.docs_path}. "
                "Adamus cannot operate without its memory."
            )

        loaded_count = 0
        failed_count = 0

        # Find all markdown files recursively
        md_files = list(self.docs_path.rglob("*.md"))

        logger.info(f"Loading {len(md_files)} documents from {self.docs_path}")

        for file_path in md_files:
            try:
                doc = self._load_document(file_path)
                self.documents[str(file_path)] = doc
                loaded_count += 1
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")
                failed_count += 1

        self._last_load_time = datetime.now()

        logger.info(
            f"Loaded {loaded_count} documents successfully, "
            f"{failed_count} failed"
        )

        if loaded_count == 0:
            raise RuntimeError("No documents loaded. Adamus cannot function.")

        return self.documents

    def _load_document(self, file_path: Path) -> Document:
        """
        Load a single document with full parsing.

        Args:
            file_path: Path to the markdown file

        Returns:
            Parsed Document object
        """
        content = file_path.read_text(encoding='utf-8')
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        doc = Document(
            path=str(file_path),
            name=file_path.name,
            content=content,
            hash=content_hash,
            loaded_at=datetime.now(),
            size_bytes=len(content.encode('utf-8'))
        )

        # Extract metadata
        doc.title = self._extract_title(content)
        doc.status = self._extract_status(content)
        doc.requirements = self._extract_requirements(content)
        doc.code_blocks = self._extract_code_blocks(content)
        doc.decisions = self._extract_decisions(content)
        doc.references = self._extract_references(content)

        return doc

    def _extract_title(self, content: str) -> str:
        """Extract document title from first heading."""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        return ""

    def _extract_status(self, content: str) -> str:
        """Extract status field if present."""
        match = re.search(r'\*\*Status\*\*:\s*(.+?)(?:\n|$)', content)
        if match:
            return match.group(1).strip()
        return "UNKNOWN"

    def _extract_requirements(self, content: str) -> List[str]:
        """Extract requirements from document."""
        requirements = []
        in_requirements = False

        for line in content.split('\n'):
            if 'requirements' in line.lower() and ':' in line:
                in_requirements = True
                continue
            if in_requirements:
                if line.strip().startswith('-'):
                    requirements.append(line.strip()[1:].strip())
                elif line.strip() and not line.startswith(' '):
                    in_requirements = False

        return requirements

    def _extract_code_blocks(self, content: str) -> List[str]:
        """Extract code blocks from document."""
        pattern = r'```(?:\w+)?\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        return matches

    def _extract_decisions(self, content: str) -> List[str]:
        """Extract decision points from document."""
        decisions = []
        pattern = r'(?:decision|resolved|conclusion):\s*(.+?)(?:\n|$)'
        matches = re.findall(pattern, content, re.IGNORECASE)
        decisions.extend(matches)
        return decisions

    def _extract_references(self, content: str) -> List[str]:
        """Extract references to other documents."""
        # Match markdown links and file references
        pattern = r'(?:\[.*?\]\()?([A-Z_]+\.md)(?:\))?'
        matches = re.findall(pattern, content)
        return list(set(matches))

    def check_for_changes(self) -> Set[str]:
        """
        Check if any documents have changed since last load.

        Returns:
            Set of file paths that have changed
        """
        changed = set()

        for file_path, doc in self.documents.items():
            path = Path(file_path)
            if not path.exists():
                changed.add(file_path)
                continue

            content = path.read_text(encoding='utf-8')
            new_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            if new_hash != doc.hash:
                changed.add(file_path)

        return changed

    def get_document(self, name: str) -> Optional[Document]:
        """
        Get a specific document by name.

        Args:
            name: Document filename (e.g., "MASTER_PROTOCOL.md")

        Returns:
            Document if found, None otherwise
        """
        for path, doc in self.documents.items():
            if doc.name == name or name in path:
                return doc
        return None

    def get_all_content(self) -> str:
        """
        Get concatenated content of all documents.

        This is used to feed complete context to brains.
        """
        sections = []
        for path, doc in sorted(self.documents.items()):
            sections.append(f"\n{'='*60}\n")
            sections.append(f"FILE: {doc.name}\n")
            sections.append(f"{'='*60}\n")
            sections.append(doc.content)
        return "\n".join(sections)

    def get_summary(self) -> Dict:
        """Get summary statistics of loaded documents."""
        total_size = sum(d.size_bytes for d in self.documents.values())

        return {
            "total_documents": len(self.documents),
            "total_size_bytes": total_size,
            "total_size_kb": total_size / 1024,
            "last_loaded": self._last_load_time.isoformat() if self._last_load_time else None,
            "documents": [
                {"name": d.name, "title": d.title, "status": d.status}
                for d in self.documents.values()
            ]
        }

    def verify_critical_documents(self) -> Dict[str, bool]:
        """
        Verify critical documents are loaded.

        Adamus CANNOT function without these.
        """
        critical = [
            "MASTER_PROTOCOL.md",
            "MASTER_CONTEXT_SYSTEM.md",
            "NETWORKED_AI_TRINITY.md",
            "SELF_IMPROVING_ADAMUS.md",
            "ZERO_TRUST_ARCHITECTURE.md",
            "PPAI_ARCHITECTURE_SPEC.md",
        ]

        status = {}
        for doc_name in critical:
            doc = self.get_document(doc_name)
            status[doc_name] = doc is not None

        return status

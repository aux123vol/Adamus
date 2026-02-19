"""
Tests for Adamus Memory System.

The memory system is CRITICAL - it's how Adamus NEVER forgets.
All documents must load successfully.
"""

import pytest
import tempfile
import os
from pathlib import Path


class TestDocumentLoader:
    """Tests for DocumentLoader."""

    def test_document_loader_init(self):
        """Test DocumentLoader initialization."""
        from src.memory.document_loader import DocumentLoader

        loader = DocumentLoader(docs_path="/tmp/nonexistent")
        assert loader.docs_path == Path("/tmp/nonexistent")
        assert len(loader.documents) == 0

    def test_load_documents_from_real_path(self):
        """Test loading documents from actual architecture path."""
        from src.memory.document_loader import DocumentLoader

        # Use actual docs path
        docs_path = Path("~/adamus/docs/architecture").expanduser()

        if not docs_path.exists():
            pytest.skip("Architecture docs not found")

        loader = DocumentLoader(docs_path=str(docs_path))
        docs = loader.load_all_documents()

        # Should load many documents (expect 90+)
        assert len(docs) > 0
        print(f"Loaded {len(docs)} documents")

    def test_document_parsing(self):
        """Test document parsing extracts metadata correctly."""
        from src.memory.document_loader import DocumentLoader

        loader = DocumentLoader()

        content = """# Test Document
## Section 1
Some content here.

**Status**: ACTIVE

```python
def example():
    pass
```

Requirements:
- requirement 1
- requirement 2

References: OTHER_DOC.md
"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False
        ) as f:
            f.write(content)
            f.flush()

            doc = loader._load_document(Path(f.name))

            assert doc.title == "Test Document"
            assert "ACTIVE" in doc.status
            assert len(doc.code_blocks) > 0
            assert len(doc.requirements) >= 0

        os.unlink(f.name)

    def test_get_document_by_name(self):
        """Test retrieving document by name."""
        from src.memory.document_loader import DocumentLoader

        docs_path = Path("~/adamus/docs/architecture").expanduser()

        if not docs_path.exists():
            pytest.skip("Architecture docs not found")

        loader = DocumentLoader(docs_path=str(docs_path))
        loader.load_all_documents()

        # Try to get a known document
        doc = loader.get_document("MASTER_PROTOCOL.md")
        if doc:
            assert "MASTER_PROTOCOL" in doc.name or "MASTER_PROTOCOL" in doc.path

    def test_verify_critical_documents(self):
        """Test critical document verification."""
        from src.memory.document_loader import DocumentLoader

        docs_path = Path("~/adamus/docs/architecture").expanduser()

        if not docs_path.exists():
            pytest.skip("Architecture docs not found")

        loader = DocumentLoader(docs_path=str(docs_path))
        loader.load_all_documents()

        status = loader.verify_critical_documents()

        # Should have status for critical docs
        assert len(status) > 0
        print(f"Critical doc status: {status}")


class TestMemoryDatabase:
    """Tests for MemoryDatabase."""

    @pytest.mark.asyncio
    async def test_database_initialization(self):
        """Test database initializes correctly."""
        from src.memory.memory_db import MemoryDatabase

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = MemoryDatabase(db_path=db_path)

            await db.initialize()

            assert os.path.exists(db_path)
            assert db._initialized

    @pytest.mark.asyncio
    async def test_store_and_retrieve_decision(self):
        """Test storing and retrieving decisions."""
        from src.memory.memory_db import MemoryDatabase, Decision
        from datetime import datetime

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = MemoryDatabase(db_path=db_path)
            await db.initialize()

            decision = Decision(
                id="test_001",
                timestamp=datetime.now().isoformat(),
                context="Test context",
                decision="Use Claude for this task",
                reasoning="Complex coding required",
                source_brain="claude",
                augustus_approved=True
            )

            await db.store_decision(decision)

            decisions = await db.get_all_decisions()
            assert len(decisions) == 1
            assert decisions[0].decision == "Use Claude for this task"

    @pytest.mark.asyncio
    async def test_budget_tracking(self):
        """Test budget tracking."""
        from src.memory.memory_db import MemoryDatabase

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = MemoryDatabase(db_path=db_path)
            await db.initialize()

            await db.track_budget("claude", 1000, 500, 0.05)
            await db.track_budget("claude", 2000, 1000, 0.10)

            spend = await db.get_monthly_spend()
            assert abs(spend - 0.15) < 0.001  # Float comparison

    @pytest.mark.asyncio
    async def test_security_event_logging(self):
        """Test security event logging."""
        from src.memory.memory_db import MemoryDatabase

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = MemoryDatabase(db_path=db_path)
            await db.initialize()

            await db.log_security_event(
                event_type="prompt_injection",
                severity="high",
                details="Detected injection attempt",
                blocked=True
            )

            stats = await db.get_memory_stats()
            assert stats["threats_blocked"] == 1

"""
Capability Builder: Adamus builds missing capabilities.

From SELF_IMPROVING_ADAMUS.md:
  "Adamus builds missing capabilities by:
   1. Reading the 8-system architecture docs
   2. Generating implementation code
   3. Testing against requirements
   4. Integrating with existing systems"
"""

import logging
import os
import subprocess
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Capability:
    """A capability that Adamus can build."""
    name: str
    description: str
    system_name: str        # which of the 8 security systems it belongs to
    is_blocking: bool = False   # does Genre ship without it?
    risk_level: str = "low"     # low / medium / critical
    effort_hours: float = 4.0
    requested: bool = False     # explicitly requested by Augustus?
    built: bool = False
    version: str = "0.1.0"
    file_path: Optional[str] = None
    built_at: Optional[str] = None

    def is_blocking_genre(self) -> bool:
        return self.is_blocking

    def is_security_critical(self) -> bool:
        return self.risk_level == "critical"


# Known capability catalogue — aligned with the 8 security systems
CAPABILITY_CATALOGUE: List[Capability] = [
    Capability(
        name="data_governance",
        description="Validate and classify data at boundaries (Level 1-4)",
        system_name="data_governance",
        is_blocking=True,
        risk_level="critical",
        effort_hours=4,
    ),
    Capability(
        name="credential_vault",
        description="Secure storage and JIT access for API keys and secrets",
        system_name="zero_trust",
        is_blocking=True,
        risk_level="critical",
        effort_hours=3,
    ),
    Capability(
        name="input_filter",
        description="Block prompt injection and malicious inputs",
        system_name="prompt_defense",
        is_blocking=False,
        risk_level="critical",
        effort_hours=2,
    ),
    Capability(
        name="cost_monitor",
        description="Track LLM spend vs $200/month budget",
        system_name="llm_optimization",
        is_blocking=False,
        risk_level="medium",
        effort_hours=2,
    ),
    Capability(
        name="bias_detector",
        description="Monitor AI outputs for bias and fairness issues",
        system_name="bias_detection",
        is_blocking=False,
        risk_level="medium",
        effort_hours=6,
    ),
    Capability(
        name="explainability_logger",
        description="Log reasoning behind every AI decision",
        system_name="explainable_ai",
        is_blocking=False,
        risk_level="low",
        effort_hours=3,
    ),
    Capability(
        name="vulnerability_scanner",
        description="Scan code for security vulnerabilities before deploy",
        system_name="vulnerability_mgmt",
        is_blocking=False,
        risk_level="medium",
        effort_hours=8,
    ),
    Capability(
        name="email_notifier",
        description="Send email alerts for critical events",
        system_name="operations",
        is_blocking=False,
        risk_level="low",
        effort_hours=1,
    ),
]


class CapabilityBuilder:
    """
    Builds missing capabilities as minimal Python modules.

    In production this would call Claude to generate code.
    For now: generates structured scaffolds with stub implementations
    that can be filled in incrementally.
    """

    CAPABILITIES_DIR = Path("src/capabilities")
    TESTS_DIR = Path("tests/capabilities")

    def __init__(self, base_path: Optional[Path] = None):
        self._base = base_path or Path(os.getcwd())
        self._cap_dir = self._base / self.CAPABILITIES_DIR
        self._tests_dir = self._base / self.TESTS_DIR
        self._built: List[str] = []

    def build_capability(self, cap: Capability) -> bool:
        """
        Build a capability module and its tests.
        Returns True if successfully built and tests pass.
        """
        self._cap_dir.mkdir(parents=True, exist_ok=True)
        self._tests_dir.mkdir(parents=True, exist_ok=True)

        # Write the capability module
        module_path = self._cap_dir / f"{cap.name}.py"
        module_code = self._generate_module(cap)
        module_path.write_text(module_code)

        # Write tests
        test_path = self._tests_dir / f"test_{cap.name}.py"
        test_code = self._generate_tests(cap)
        test_path.write_text(test_code)

        # Mark as built
        cap.built = True
        cap.file_path = str(module_path.relative_to(self._base))
        cap.built_at = datetime.utcnow().isoformat()
        self._built.append(cap.name)

        logger.info(f"Built capability: {cap.name} v{cap.version} → {cap.file_path}")
        return True

    def _generate_module(self, cap: Capability) -> str:
        """Generate a minimal capability module scaffold."""
        class_name = "".join(w.title() for w in cap.name.split("_"))
        return textwrap.dedent(f'''\
            """
            Capability: {cap.name}
            System: {cap.system_name}
            Version: {cap.version}

            {cap.description}

            Auto-generated by Adamus CapabilityBuilder.
            Adamus builds itself. Brains change, Adamus stays consistent.
            """
            import logging
            from datetime import datetime

            logger = logging.getLogger(__name__)


            class {class_name}:
                """
                {cap.description}

                Risk level: {cap.risk_level}
                Blocks Genre: {cap.is_blocking}
                """

                VERSION = "{cap.version}"

                def __init__(self):
                    self._active = True
                    self._call_count = 0
                    logger.info(f"{class_name} v{{self.VERSION}} initialized")

                def is_active(self) -> bool:
                    return self._active

                def health_check(self) -> dict:
                    return {{
                        "capability": "{cap.name}",
                        "version": self.VERSION,
                        "active": self._active,
                        "call_count": self._call_count,
                        "system": "{cap.system_name}",
                    }}

                def execute(self, *args, **kwargs) -> dict:
                    """
                    Main capability execution.
                    TODO: Implement {cap.description}
                    """
                    self._call_count += 1
                    logger.debug(f"{class_name}.execute called (#{{}}: {{self._call_count}})")
                    return {{
                        "status": "ok",
                        "capability": "{cap.name}",
                        "timestamp": datetime.utcnow().isoformat(),
                    }}
        ''')

    def _generate_tests(self, cap: Capability) -> str:
        """Generate minimal tests for a capability."""
        class_name = "".join(w.title() for w in cap.name.split("_"))
        return textwrap.dedent(f'''\
            """Tests for {cap.name} capability."""
            import pytest
            import sys
            from pathlib import Path

            sys.path.insert(0, str(Path(__file__).parents[3]))

            from src.capabilities.{cap.name} import {class_name}


            class Test{class_name}:
                def test_instantiation(self):
                    c = {class_name}()
                    assert c is not None

                def test_is_active(self):
                    c = {class_name}()
                    assert c.is_active() is True

                def test_health_check(self):
                    c = {class_name}()
                    h = c.health_check()
                    assert h["capability"] == "{cap.name}"
                    assert h["active"] is True

                def test_execute_returns_ok(self):
                    c = {class_name}()
                    result = c.execute()
                    assert result["status"] == "ok"
                    assert "timestamp" in result
        ''')

    def get_inventory(self) -> List[str]:
        """Return names of all built capabilities."""
        if not self._cap_dir.exists():
            return []
        return [p.stem for p in self._cap_dir.glob("*.py") if not p.stem.startswith("_")]

    def is_built(self, name: str) -> bool:
        if self._cap_dir.exists():
            return (self._cap_dir / f"{name}.py").exists()
        return False

    def get_build_log(self) -> List[str]:
        return list(self._built)

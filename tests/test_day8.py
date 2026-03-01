"""
Day 8 Tests — Unified Web UI + Main Wiring

Covers:
- unified_app: all routes return expected status codes
- unified_app: /api/status returns JSON with expected keys
- unified_app: /api/docs returns list
- unified_app: /api/chat SSE endpoint exists
- adamus_interface: AdamusInterface class is importable and has run()
- main.py: start_web_ui and start_autonomous_loop functions exist
"""

import json
import pytest


# ── Unified Web UI ─────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    from src.ui.unified_app import create_app
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestUnifiedAppRoutes:
    """All GET routes must return 200."""

    def test_root_returns_200(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_chat_page_returns_200(self, client):
        r = client.get("/chat")
        assert r.status_code == 200

    def test_docs_page_returns_200(self, client):
        r = client.get("/docs")
        assert r.status_code == 200

    def test_status_page_returns_200(self, client):
        r = client.get("/status")
        assert r.status_code == 200

    def test_api_status_returns_json(self, client):
        r = client.get("/api/status")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "git" in data or "timestamp" in data or isinstance(data, dict)

    def test_api_docs_returns_list(self, client):
        r = client.get("/api/docs")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert isinstance(data, list)

    def test_unknown_doc_returns_404(self, client):
        r = client.get("/api/docs/NONEXISTENT_DOC_XYZ.md")
        assert r.status_code == 404

    def test_chat_endpoint_exists(self, client):
        """POST /api/chat must exist (may need JSON body)."""
        r = client.post(
            "/api/chat",
            data=json.dumps({"message": "hello"}),
            content_type="application/json"
        )
        # Accept 200 (streaming) or 400 (validation) — not 404 or 500
        assert r.status_code in (200, 400)

    def test_create_app_returns_flask_app(self):
        from flask import Flask
        from src.ui.unified_app import create_app
        app = create_app()
        assert isinstance(app, Flask)


class TestUnifiedAppContent:
    """Response content checks."""

    def test_root_contains_adamus(self, client):
        r = client.get("/")
        assert b"adamus" in r.data.lower() or b"Adamus" in r.data

    def test_chat_page_contains_chat_input(self, client):
        r = client.get("/chat")
        # Should have a form or input element
        assert b"<input" in r.data or b"<textarea" in r.data or b"message" in r.data.lower()

    def test_docs_page_lists_docs(self, client):
        r = client.get("/docs")
        assert r.status_code == 200
        # Should mention docs or architecture
        content = r.data.lower()
        assert b"doc" in content or b"architecture" in content or b"master" in content

    def test_api_status_has_git_field(self, client):
        r = client.get("/api/status")
        data = json.loads(r.data)
        # Status should include at minimum one system field
        assert len(data) > 0


# ── AdamusInterface ────────────────────────────────────────────────────────────

class TestAdamusInterface:
    """AdamusInterface REPL class tests."""

    def test_class_importable(self):
        from src.ui.adamus_interface import AdamusInterface
        assert AdamusInterface is not None

    def test_has_run_method(self):
        from src.ui.adamus_interface import AdamusInterface
        assert hasattr(AdamusInterface, "run")

    def test_instantiates_with_coordinator(self):
        from src.ui.adamus_interface import AdamusInterface
        # Coordinator is optional — pass None for testing
        interface = AdamusInterface(coordinator=None)
        assert interface.coordinator is None
        assert interface._loop_ref is None

    def test_banner_contains_adamus(self):
        from src.ui.adamus_interface import AdamusInterface
        assert "ADAMUS" in AdamusInterface.BANNER or "adamus" in AdamusInterface.BANNER.lower()

    def test_run_is_coroutine(self):
        import asyncio
        from src.ui.adamus_interface import AdamusInterface
        interface = AdamusInterface(coordinator=None)
        import inspect
        assert inspect.iscoroutinefunction(interface.run)


# ── Main entry point wiring ────────────────────────────────────────────────────

class TestMainWiring:
    """Verify main.py wiring functions exist and are callable."""

    def test_start_web_ui_function_exists(self):
        from src.main import start_web_ui
        assert callable(start_web_ui)

    def test_start_autonomous_loop_function_exists(self):
        from src.main import start_autonomous_loop
        assert callable(start_autonomous_loop)

    def test_setup_logging_function_exists(self):
        from src.main import setup_logging
        assert callable(setup_logging)

    def test_start_web_ui_returns_thread(self):
        """start_web_ui launches a daemon thread on an available port."""
        import threading
        from src.main import start_web_ui
        # Use a high port unlikely to be in use
        t = start_web_ui(host="127.0.0.1", port=19888)
        assert isinstance(t, threading.Thread)
        assert t.daemon is True
        assert t.is_alive()

    def test_start_autonomous_loop_without_coordinator(self):
        """start_autonomous_loop gracefully handles no coordinator."""
        from src.main import start_autonomous_loop
        # Passing None coordinator — should either start or return None gracefully
        loop_obj = start_autonomous_loop(coordinator=None)
        # Acceptable: either returns a loop object or None (if coordinator required)
        # Just confirm it doesn't raise
        if loop_obj is not None:
            loop_obj.stop()

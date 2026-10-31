"""Browser suite runs explicitly; the default tests/ suite needs no browser."""
import socket
import threading
import time

import pytest
import uvicorn

from qa_pipeline.api import create_app


@pytest.fixture
def isolated_review_api(tmp_path):
    # Synthetic source and SQLite state, independent of private files or env vars.
    source = tmp_path / "requirements.md"
    source.write_text(
        "# Browser Test Requirements\n"
        "**Document version:** 1.0\n\n"
        "## Guest access\n"
        "**AUTH-04** Browse the public landing page and use Features, About Us, "
        "How It Works, and Roadmap navigation without connecting a wallet.\n\n"
        "## Accessibility\n"
        "**ACCESS-01** Keyboard navigation must reach the mobile menu trigger "
        "with visible focus and support Enter and Space activation.\n",
        encoding="utf-8",
    )
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(
        create_app(source_path=source, review_path=tmp_path / "reviews.sqlite3"),
        log_level="error"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 5
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.05)
        assert server.started, "Isolated review API did not start"
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        sock.close()

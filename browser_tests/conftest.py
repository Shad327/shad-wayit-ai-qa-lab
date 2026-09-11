"""Browser suite runs explicitly; the default tests/ suite needs no browser."""
import socket
import threading
import time

import pytest
import uvicorn

from qa_pipeline.api import create_app


@pytest.fixture
def isolated_review_api(tmp_path):
    # Real HTTP API + SQLite, isolated from the owner's saved reviews.
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(
        create_app(review_path=tmp_path / "reviews.sqlite3"), log_level="error"))
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

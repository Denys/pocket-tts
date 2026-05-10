"""Lightweight Windows starter for the local Pocket TTS web app."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from collections.abc import Mapping
from pathlib import Path


def resolve_repo_root(start: Path | None = None) -> Path:
    """Find the source checkout that owns the venv and package entrypoint."""

    if start is None:
        if getattr(sys, "frozen", False):
            start = Path(sys.executable).resolve().parent
        else:
            start = Path(__file__).resolve().parent

    start = Path(start).resolve()
    for candidate in (start, *start.parents):
        if _is_repo_root(candidate):
            return candidate

    raise RuntimeError(
        "Could not find the Pocket TTS checkout. Expected .venv/Scripts/python.exe "
        "and pocket_tts/main.py near this starter."
    )


def _is_repo_root(path: Path) -> bool:
    return (
        (path / ".venv" / "Scripts" / "python.exe").exists()
        and (path / "pocket_tts" / "main.py").exists()
    )


def sanitize_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return a Windows-safe environment with only one canonical Path key."""

    source = source or os.environ
    env: dict[str, str] = {}
    for key, value in source.items():
        normalized_key = "Path" if key.lower() == "path" else key
        if normalized_key not in env:
            env[normalized_key] = value

    return env


def build_server_command(repo_root: Path, *, host: str, port: int) -> list[str]:
    python_exe = repo_root / ".venv" / "Scripts" / "python.exe"
    return [
        str(python_exe),
        "-m",
        "pocket_tts",
        "serve",
        "--host",
        host,
        "--port",
        str(port),
    ]


def wait_for_health(url: str, *, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return True
        except (OSError, urllib.error.URLError):
            time.sleep(0.5)

    return False


def start_server(repo_root: Path, *, host: str, port: int) -> subprocess.Popen[bytes]:
    tmp_dir = repo_root / ".tmp"
    tmp_dir.mkdir(exist_ok=True)
    stdout = (tmp_dir / "pocket-tts-starter-server.out.log").open("ab", buffering=0)
    stderr = (tmp_dir / "pocket-tts-starter-server.err.log").open("ab", buffering=0)
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    return subprocess.Popen(
        build_server_command(repo_root, host=host, port=port),
        cwd=repo_root,
        env=sanitize_environment(),
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=stderr,
        close_fds=True,
        creationflags=creationflags,
    )


def run_starter(*, host: str, port: int, path: str, timeout_seconds: float) -> int:
    repo_root = resolve_repo_root()
    base_url = f"http://{host}:{port}"
    health_url = f"{base_url}/health"
    app_url = f"{base_url}{path}"

    if wait_for_health(health_url, timeout_seconds=1):
        webbrowser.open(app_url)
        return 0

    process = start_server(repo_root, host=host, port=port)
    if not wait_for_health(health_url, timeout_seconds=timeout_seconds):
        process.terminate()
        raise RuntimeError(f"Pocket TTS server did not become ready at {health_url}")

    webbrowser.open(app_url)
    try:
        return process.wait()
    except KeyboardInterrupt:
        process.terminate()
        return 130


def main() -> None:
    parser = argparse.ArgumentParser(description="Start Pocket TTS localhost and open the web UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--path", default="/", choices=("/", "/glass"))
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()

    raise SystemExit(
        run_starter(host=args.host, port=args.port, path=args.path, timeout_seconds=args.timeout)
    )


if __name__ == "__main__":
    main()

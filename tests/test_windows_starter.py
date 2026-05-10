"""Tests for the lightweight Windows web starter."""

from pathlib import Path

from scripts.pocket_tts_web_starter import (
    build_server_command,
    resolve_repo_root,
    sanitize_environment,
)


def test_resolve_repo_root_from_packaged_starter_directory(tmp_path):
    repo = tmp_path / "pocket-tts"
    starter_dir = repo / "dist" / "windows" / "Pocket TTS Starter"
    python_exe = repo / ".venv" / "Scripts" / "python.exe"
    main_py = repo / "pocket_tts" / "main.py"
    starter_dir.mkdir(parents=True)
    python_exe.parent.mkdir(parents=True)
    main_py.parent.mkdir(parents=True)
    python_exe.write_text("", encoding="utf-8")
    main_py.write_text("", encoding="utf-8")

    assert resolve_repo_root(starter_dir) == repo


def test_sanitize_environment_keeps_single_canonical_path_key():
    env = sanitize_environment({"PATH": "first", "Path": "second", "OTHER": "value"})

    assert env["Path"] == "first"
    assert env["OTHER"] == "value"
    assert "PATH" not in env


def test_build_server_command_uses_repo_virtualenv_python(tmp_path):
    repo = tmp_path
    python_exe = repo / ".venv" / "Scripts" / "python.exe"
    python_exe.parent.mkdir(parents=True)
    python_exe.write_text("", encoding="utf-8")

    command = build_server_command(repo, host="127.0.0.1", port=8000)

    assert command == [
        str(python_exe),
        "-m",
        "pocket_tts",
        "serve",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]

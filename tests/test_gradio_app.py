"""Tests for the optional Gradio UI entry point."""

import types
from pathlib import Path

from typer.testing import CliRunner

from pocket_tts.main import cli_app


class FakeModel:
    def __init__(self):
        self.config = types.SimpleNamespace(mimi=types.SimpleNamespace(sample_rate=24000))
        self.origin = "english"
        self.voice_requests = []
        self.generated_requests = []

    def get_state_for_audio_prompt(self, voice, truncate=False):
        self.voice_requests.append((voice, truncate))
        return {"voice": voice}

    def generate_audio_stream(self, model_state, text_to_generate, frames_after_eos=None):
        self.generated_requests.append((model_state, text_to_generate, frames_after_eos))
        return iter(["chunk"])


def test_gradio_voice_choices_put_default_voice_first():
    from pocket_tts.gradio_app import get_builtin_voice_choices

    choices = get_builtin_voice_choices("italian")

    assert choices[0] == "giovanni"
    assert "alba" in choices
    assert choices == sorted(set(choices), key=lambda voice: (voice != "giovanni", voice))


def test_resolve_voice_source_prefers_uploaded_voice_over_custom_and_builtin():
    from pocket_tts.gradio_app import resolve_voice_source

    source, truncate = resolve_voice_source(
        builtin_voice="alba",
        custom_voice="https://example.test/voice.wav",
        uploaded_voice="C:/tmp/reference.wav",
        language="english",
    )

    assert source == "C:/tmp/reference.wav"
    assert truncate is True


def test_generate_audio_file_writes_temp_wav_with_selected_voice(tmp_path, monkeypatch):
    from pocket_tts import gradio_app

    model = FakeModel()
    output_dir = tmp_path / "outputs"
    writes = []

    def fake_stream_audio_chunks(output_path, audio_chunks, sample_rate):
        writes.append((output_path, list(audio_chunks), sample_rate))
        output_path.write_bytes(b"RIFF generated wav")

    monkeypatch.setattr(gradio_app, "stream_audio_chunks", fake_stream_audio_chunks)

    output_path, status = gradio_app.generate_audio_file(
        model=model,
        text="Hello from Gradio.",
        builtin_voice="alba",
        custom_voice="",
        uploaded_voice=None,
        output_dir=output_dir,
    )

    assert output_path.exists()
    assert output_path.parent == output_dir
    assert output_path.suffix == ".wav"
    assert "Generated" in status
    assert model.voice_requests == [("alba", False)]
    assert model.generated_requests == [({"voice": "alba"}, "Hello from Gradio.", None)]
    assert writes == [(output_path, ["chunk"], 24000)]


def test_gradio_cli_delegates_to_launcher(monkeypatch):
    import pocket_tts.main as main

    calls = []

    def fake_launch_gradio_app(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(main, "launch_gradio_app", fake_launch_gradio_app)

    result = CliRunner().invoke(
        cli_app,
        ["gradio", "--host", "127.0.0.1", "--port", "7861", "--language", "english"],
    )

    assert result.exit_code == 0
    assert calls == [
        {
            "host": "127.0.0.1",
            "port": 7861,
            "language": "english",
            "config": None,
            "quantize": False,
        }
    ]


def test_windows_gradio_launcher_forwards_language_arguments():
    launcher = Path("Pocket-TTS-Gradio.bat").read_text(encoding="utf-8")

    assert "pocket_tts gradio --host 127.0.0.1 --port 7860 %*" in launcher
    assert "pocket-tts gradio --host 127.0.0.1 --port 7860 %*" in launcher


def test_gradio_shortcut_helper_can_create_italian_launcher_arguments():
    shortcut_script = Path("scripts/create_gradio_shortcuts.ps1").read_text(encoding="utf-8")

    assert '[string]$Language = "italian"' in shortcut_script
    assert '$Shortcut.Arguments = "--language $Language"' in shortcut_script
    assert '-ArgumentList "--language $Language"' in shortcut_script


def test_gradio_css_uses_glass_visual_language():
    from pocket_tts.gradio_app import _GRADIO_CSS

    assert "Afacad Flux" in _GRADIO_CSS
    assert "Fraunces" in _GRADIO_CSS
    assert "#root" in _GRADIO_CSS
    assert "radial-gradient(circle at 8% 6%" in _GRADIO_CSS
    assert "backdrop-filter: blur(28px)" in _GRADIO_CSS
    assert "--pocket-teal: #7cf7dd" in _GRADIO_CSS
    assert "--pocket-amber: #ffd166" in _GRADIO_CSS
    assert "--pocket-rose: #ff7ca8" in _GRADIO_CSS
    assert "--pocket-blue: #8eb9ff" in _GRADIO_CSS
    assert ".studio-panel::after" in _GRADIO_CSS
    assert ".studio-panel .studio-panel" in _GRADIO_CSS
    assert ".primary-action button" in _GRADIO_CSS
    assert ".download-action button" in _GRADIO_CSS


def test_gradio_launcher_applies_glass_theme_css(monkeypatch):
    from pocket_tts import gradio_app

    fake_gradio = types.SimpleNamespace(
        themes=types.SimpleNamespace(Soft=lambda: "soft-theme")
    )
    fake_model = FakeModel()
    launch_calls = []

    class FakeDemo:
        def launch(self, **kwargs):
            launch_calls.append(kwargs)

    def fake_create_gradio_app(model, language, gradio_module):
        assert model is fake_model
        assert language is None
        assert gradio_module is fake_gradio
        return FakeDemo()

    monkeypatch.setattr(gradio_app, "_import_gradio", lambda: fake_gradio)
    monkeypatch.setattr(gradio_app, "create_gradio_app", fake_create_gradio_app)

    gradio_app.launch_gradio_app(model_loader=lambda **kwargs: fake_model)

    assert launch_calls == [
        {
            "server_name": "127.0.0.1",
            "server_port": 7860,
            "theme": "soft-theme",
            "css": gradio_app._GRADIO_CSS,
        }
    ]


def test_launcher_checks_gradio_dependency_before_loading_model(monkeypatch):
    from pocket_tts import gradio_app

    def missing_gradio():
        raise RuntimeError("missing gradio")

    def fail_model_loader(**kwargs):
        raise AssertionError("Model should not load before Gradio dependency is available")

    monkeypatch.setattr(gradio_app, "_import_gradio", missing_gradio)

    try:
        gradio_app.launch_gradio_app(model_loader=fail_model_loader)
    except RuntimeError as exc:
        assert str(exc) == "missing gradio"
    else:
        raise AssertionError("Expected missing Gradio dependency to raise RuntimeError")

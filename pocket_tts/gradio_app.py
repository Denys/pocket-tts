"""Optional Gradio UI for Pocket TTS."""

import tempfile
import uuid
from pathlib import Path
from typing import Any

from pocket_tts.data.audio import stream_audio_chunks
from pocket_tts.default_parameters import (
    MAX_TOKEN_PER_CHUNK,
    get_default_text_for_language,
    get_default_voice_for_language,
)
from pocket_tts.models.tts_model import TTSModel
from pocket_tts.utils.utils import _ORIGINS_OF_PREDEFINED_VOICES


GRADIO_MISSING_MESSAGE = (
    "The Gradio UI requires the optional Gradio dependency. "
    "Install it with: pip install 'pocket-tts[gradio]'"
)


def get_builtin_voice_choices(language: str | None) -> list[str]:
    """Return built-in voice names with the language default first."""
    default_voice = get_default_voice_for_language(language)
    voices = set(_ORIGINS_OF_PREDEFINED_VOICES)
    voices.add(default_voice)
    return sorted(voices, key=lambda voice: (voice != default_voice, voice))


def resolve_voice_source(
    builtin_voice: str | None,
    custom_voice: str | None,
    uploaded_voice: str | Path | None,
    language: str | None,
) -> tuple[str | Path, bool]:
    """Resolve Gradio voice controls to a Pocket TTS voice source.

    Uploaded reference audio deliberately takes priority over custom URL/name and the built-in
    dropdown, matching the existing local web UI behavior.
    """
    uploaded_voice_path = _coerce_uploaded_path(uploaded_voice)
    if uploaded_voice_path is not None:
        return uploaded_voice_path, True

    if custom_voice is not None and custom_voice.strip():
        return custom_voice.strip(), False

    if builtin_voice is not None and builtin_voice.strip():
        return builtin_voice.strip(), False

    return get_default_voice_for_language(language), False


def generate_audio_file(
    model: Any,
    text: str,
    builtin_voice: str | None,
    custom_voice: str | None,
    uploaded_voice: str | Path | None,
    output_dir: str | Path | None = None,
) -> tuple[Path, str]:
    """Generate one WAV file and return its path plus a concise status string."""
    text = text.strip()
    if not text:
        raise ValueError("Enter text before generating audio.")

    language = str(model.origin) if getattr(model, "origin", None) is not None else None
    voice_source, truncate_voice = resolve_voice_source(
        builtin_voice=builtin_voice,
        custom_voice=custom_voice,
        uploaded_voice=uploaded_voice,
        language=language,
    )
    model_state = model.get_state_for_audio_prompt(voice_source, truncate=truncate_voice)

    target_dir = Path(output_dir) if output_dir is not None else Path(
        tempfile.mkdtemp(prefix="pocket-tts-gradio-")
    )
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / f"pocket-tts-{uuid.uuid4().hex[:12]}.wav"

    audio_chunks = model.generate_audio_stream(model_state=model_state, text_to_generate=text)
    stream_audio_chunks(output_path, audio_chunks, model.config.mimi.sample_rate)

    return output_path, f"Generated {output_path.name}"


def create_gradio_app(
    model: Any,
    language: str | None = None,
    gradio_module: Any | None = None,
):
    """Build the Gradio Blocks app around an already loaded model."""
    gr = gradio_module or _import_gradio()
    model_language = language or (
        str(model.origin) if getattr(model, "origin", None) is not None else None
    )
    voice_choices = get_builtin_voice_choices(model_language)
    default_voice = get_default_voice_for_language(model_language)

    def load_text_file(text_file: str | Path | None) -> str:
        if text_file is None:
            return ""
        return Path(text_file).read_text(encoding="utf-8")

    def run_generation(
        text: str,
        builtin_voice: str | None,
        custom_voice: str | None,
        uploaded_voice: str | Path | None,
        progress=gr.Progress(),
    ):
        progress(0.05, desc="Preparing voice")
        output_path, status = generate_audio_file(
            model=model,
            text=text,
            builtin_voice=builtin_voice,
            custom_voice=custom_voice,
            uploaded_voice=uploaded_voice,
        )
        progress(1.0, desc="Ready")
        return output_path, status, output_path

    with gr.Blocks(title="Pocket TTS Glass Studio", fill_width=True) as demo:
        gr.Markdown(
            "# Pocket TTS Glass Studio\n"
            "Glassmorphism voice drafting surface for local CPU synthesis.",
            elem_classes=["studio-hero"],
        )

        with gr.Row(equal_height=True, elem_classes=["studio-layout"]):
            with gr.Column(scale=3, elem_classes=["studio-column"]):
                with gr.Group(elem_classes=["studio-panel", "script-panel"]):
                    text_input = gr.Textbox(
                        label="Script",
                        value=get_default_text_for_language(model_language),
                        lines=12,
                        max_lines=18,
                        placeholder="Paste text to synthesize...",
                        elem_classes=["script-input"],
                    )
                    text_file = gr.File(
                        label="Load .txt script",
                        file_types=[".txt"],
                        type="filepath",
                        elem_classes=["glass-file-input"],
                    )
                    gr.Markdown(
                        f"No hard character limit is enforced; generation is chunked around "
                        f"{MAX_TOKEN_PER_CHUNK} tokenizer tokens.",
                        elem_classes=["hint-copy"],
                    )

                with gr.Group(elem_classes=["studio-panel", "source-panel"]):
                    custom_voice = gr.Textbox(
                        label="Custom voice URL or name",
                        placeholder="hf://, https://, local path, or built-in name",
                    )
                    uploaded_voice = gr.Audio(
                        label="Uploaded reference voice",
                        sources=["upload", "microphone"],
                        type="filepath",
                    )
                    gr.Markdown(
                        "Uploaded audio takes precedence over custom and built-in voices.",
                        elem_classes=["hint-copy"],
                    )

            with gr.Column(scale=2, elem_classes=["studio-column"]):
                with gr.Group(elem_classes=["studio-panel", "voice-panel"]):
                    builtin_voice = gr.Dropdown(
                        choices=voice_choices,
                        value=default_voice,
                        label="Built-in voice",
                    )
                    gr.Markdown(
                        "Voice priority: uploaded audio > custom voice > built-in voice.",
                        elem_classes=["hint-copy"],
                    )

                with gr.Group(elem_classes=["studio-panel", "generate-panel"]):
                    generate_button = gr.Button(
                        "Generate audio",
                        variant="primary",
                        elem_classes=["primary-action"],
                    )
                    status = gr.Textbox(
                        label="Status",
                        interactive=False,
                        elem_classes=["status-field"],
                    )
                    generated_audio = gr.Audio(
                        label="Generated speech",
                        type="filepath",
                        interactive=False,
                    )
                    download = gr.DownloadButton("Download WAV", elem_classes=["download-action"])

        with gr.Accordion(
            "Built-in voice catalog", open=False, elem_classes=["voice-catalog"]
        ):
            gr.Dataframe(
                value=[[voice] for voice in voice_choices],
                headers=["Voice"],
                interactive=False,
                wrap=True,
            )

        text_file.change(load_text_file, inputs=text_file, outputs=text_input)
        generate_button.click(
            run_generation,
            inputs=[text_input, builtin_voice, custom_voice, uploaded_voice],
            outputs=[generated_audio, status, download],
            concurrency_limit=1,
        )

    demo.queue(default_concurrency_limit=1)
    return demo


def launch_gradio_app(
    host: str = "127.0.0.1",
    port: int = 7860,
    language: str | None = None,
    config: str | None = None,
    quantize: bool = False,
    model_loader=None,
) -> None:
    """Load the model and start the Gradio app."""
    gr = _import_gradio()
    model_loader = model_loader or TTSModel.load_model
    model = model_loader(language=language, config=config, quantize=quantize)
    demo = create_gradio_app(model, language=language, gradio_module=gr)
    demo.launch(server_name=host, server_port=port, theme=gr.themes.Soft(), css=_GRADIO_CSS)


def _coerce_uploaded_path(uploaded_voice: str | Path | None) -> str | Path | None:
    if uploaded_voice is None:
        return None
    if isinstance(uploaded_voice, str) and not uploaded_voice.strip():
        return None
    return uploaded_voice


def _import_gradio():
    try:
        import gradio as gr
    except ImportError as exc:
        raise RuntimeError(GRADIO_MISSING_MESSAGE) from exc
    return gr


_GRADIO_CSS = """
@import url("https://fonts.googleapis.com/css2?family=Afacad+Flux:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap");

:root {
    color-scheme: dark;
    --pocket-ink: #071016;
    --pocket-panel: rgba(255, 255, 255, 0.12);
    --pocket-panel-strong: rgba(255, 255, 255, 0.18);
    --pocket-line: rgba(255, 255, 255, 0.22);
    --pocket-text: #f5fbff;
    --pocket-muted: rgba(245, 251, 255, 0.68);
    --pocket-faint: rgba(245, 251, 255, 0.48);
    --pocket-teal: #7cf7dd;
    --pocket-amber: #ffd166;
    --pocket-rose: #ff7ca8;
    --pocket-blue: #8eb9ff;
    --pocket-danger: #ff9b9b;
    --pocket-shadow: 0 24px 80px rgba(0, 0, 0, 0.38);
    --pocket-radius: 28px;
}

html {
    min-height: 100%;
    background: #05070c !important;
}

body,
#root,
gradio-app {
    min-height: 100vh !important;
    background:
        radial-gradient(circle at 8% 6%, rgba(124, 247, 221, 0.32), transparent 28rem),
        radial-gradient(circle at 88% 12%, rgba(255, 124, 168, 0.24), transparent 26rem),
        radial-gradient(circle at 60% 96%, rgba(255, 209, 102, 0.22), transparent 24rem),
        linear-gradient(135deg, #061018 0%, #121922 45%, #05070c 100%) !important;
    color: var(--pocket-text) !important;
    font-family: "Afacad Flux", "Segoe UI", sans-serif !important;
    letter-spacing: 0 !important;
}

body::before,
#root::before {
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    content: "";
    opacity: 0.36;
    background-image:
        linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
    background-size: 64px 64px;
    mask-image: radial-gradient(circle at 50% 20%, black, transparent 74%);
}

.gradio-container {
    position: relative;
    z-index: 1;
    max-width: min(1180px, calc(100vw - 32px)) !important;
    min-height: 100vh !important;
    margin: 0 auto !important;
    padding: 12px 0 24px !important;
    background: transparent !important;
    color: var(--pocket-text) !important;
    font-family: "Afacad Flux", "Segoe UI", sans-serif !important;
    --body-background-fill: transparent;
    --background-fill-primary: transparent;
    --background-fill-secondary: transparent;
    --block-background-fill: rgba(255, 255, 255, 0.1);
    --block-border-color: rgba(255, 255, 255, 0.2);
    --border-color-primary: rgba(255, 255, 255, 0.2);
    --input-background-fill: rgba(4, 10, 15, 0.38);
    --input-border-color: rgba(255, 255, 255, 0.2);
    --body-text-color: var(--pocket-text);
    --body-text-color-subdued: var(--pocket-muted);
    --link-text-color: var(--pocket-teal);
    --button-primary-background-fill: linear-gradient(
        135deg,
        var(--pocket-teal),
        var(--pocket-amber)
    );
    --button-primary-text-color: var(--pocket-ink);
}

.gradio-container,
.gradio-container * {
    letter-spacing: 0 !important;
}

.gradio-container .contain,
.gradio-container .main,
.gradio-container .app,
.gradio-container .wrap,
.gradio-container main,
.gradio-container footer {
    background: transparent !important;
}

.gradio-container footer {
    display: none !important;
}

.gradio-container .block,
.gradio-container .form,
.gradio-container .panel {
    background: transparent !important;
    border-color: transparent !important;
    box-shadow: none !important;
}

.studio-hero {
    margin-bottom: 10px !important;
}

.studio-hero h1 {
    margin: 0 !important;
    color: var(--pocket-text) !important;
    font-family: "Fraunces", Georgia, serif !important;
    font-size: clamp(1.45rem, 2.6vw, 2.2rem) !important;
    line-height: 0.95 !important;
}

.studio-hero p {
    margin-top: 6px !important;
    color: var(--pocket-muted) !important;
    font-size: 0.96rem !important;
}

.studio-layout {
    align-items: stretch !important;
    gap: 12px !important;
}

.studio-column {
    min-width: 0 !important;
    gap: 12px !important;
}

.studio-panel {
    position: relative !important;
    min-width: 280px !important;
    overflow: visible !important;
    padding: 16px !important;
    border: 1px solid var(--pocket-line) !important;
    border-radius: var(--pocket-radius) !important;
    background:
        linear-gradient(145deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.07)),
        var(--pocket-panel) !important;
    box-shadow: var(--pocket-shadow), inset 0 1px 0 rgba(255, 255, 255, 0.22) !important;
    backdrop-filter: blur(28px) saturate(1.18) !important;
}

.studio-panel::after {
    position: absolute;
    inset: 0;
    pointer-events: none;
    content: "";
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.18), transparent 34%);
    opacity: 0.58;
}

.studio-panel .studio-panel {
    min-width: 0 !important;
    padding: 0 !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    backdrop-filter: none !important;
}

.studio-panel .studio-panel::after {
    display: none !important;
}

.studio-panel > * {
    position: relative !important;
    z-index: 1 !important;
}

.studio-panel .block,
.studio-panel .form {
    background: transparent !important;
}

.studio-panel .block {
    margin-bottom: 10px !important;
}

.gradio-container label,
.gradio-container .block-title,
.gradio-container .block-label,
.gradio-container .label-wrap span,
.gradio-container .wrap label span {
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 8px !important;
    color: rgba(245, 251, 255, 0.84) !important;
    background: rgba(142, 185, 255, 0.18) !important;
    font-size: 0.9rem !important;
    font-weight: 700 !important;
}

.hint-copy,
.hint-copy p,
.gradio-container .info,
.gradio-container .secondary-text {
    color: var(--pocket-muted) !important;
    font-size: 0.9rem !important;
    white-space: normal !important;
    overflow: visible !important;
    overflow-wrap: anywhere !important;
}

.hint-copy {
    padding-top: 4px !important;
}

.gradio-container textarea,
.gradio-container input,
.gradio-container select {
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 18px !important;
    outline: none !important;
    color: var(--pocket-text) !important;
    background: rgba(4, 10, 15, 0.38) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06) !important;
    font-family: "Afacad Flux", "Segoe UI", sans-serif !important;
}

.gradio-container textarea {
    min-height: 180px !important;
    line-height: 1.55 !important;
    font-size: 0.98rem !important;
}

.gradio-container input::placeholder,
.gradio-container textarea::placeholder {
    color: var(--pocket-faint) !important;
}

.gradio-container select option {
    color: #111820 !important;
}

.gradio-container button,
.gradio-container .download-action,
.gradio-container .download-action button {
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 18px !important;
    color: var(--pocket-text) !important;
    background: rgba(255, 255, 255, 0.1) !important;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.15),
        0 16px 38px rgba(0, 0, 0, 0.24) !important;
    font-family: "Afacad Flux", "Segoe UI", sans-serif !important;
    font-weight: 700 !important;
    transition: transform 160ms ease, background 160ms ease, border-color 160ms ease !important;
}

.gradio-container button:hover:not(:disabled) {
    transform: translateY(-1px);
    background: rgba(255, 255, 255, 0.16) !important;
    border-color: rgba(255, 255, 255, 0.32) !important;
}

.gradio-container button.primary,
.gradio-container .primary-action button,
.gradio-container button.primary-action {
    min-height: 46px !important;
    color: var(--pocket-ink) !important;
    background: linear-gradient(135deg, var(--pocket-teal), var(--pocket-amber)) !important;
    border-color: rgba(255, 255, 255, 0.42) !important;
    font-size: 1.03rem !important;
}

.gradio-container .download-action button,
.gradio-container button.download-action {
    min-height: 42px !important;
    color: var(--pocket-ink) !important;
    background: linear-gradient(135deg, var(--pocket-teal), var(--pocket-blue)) !important;
    border-color: rgba(255, 255, 255, 0.38) !important;
}

.status-field textarea,
.status-field input {
    min-height: 46px !important;
    color: var(--pocket-muted) !important;
}

.gradio-container audio {
    width: 100% !important;
    filter: drop-shadow(0 12px 32px rgba(0, 0, 0, 0.28)) !important;
}

.voice-catalog {
    margin-top: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    border-radius: 22px !important;
    background: rgba(255, 255, 255, 0.08) !important;
    backdrop-filter: blur(18px) !important;
}

.voice-catalog table,
.voice-catalog th,
.voice-catalog td {
    color: var(--pocket-text) !important;
    background: transparent !important;
}

@media (max-width: 860px) {
    .gradio-container {
        max-width: min(100vw - 24px, 680px) !important;
        padding-top: 12px !important;
    }

    .studio-layout {
        flex-direction: column !important;
    }

    .studio-panel {
        min-width: 0 !important;
        border-radius: 22px !important;
    }
}
"""

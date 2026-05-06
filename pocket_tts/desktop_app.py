"""Desktop launcher for the local Pocket TTS web interface."""

from __future__ import annotations

import logging
import socket
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import uvicorn

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DesktopAppOptions:
    host: str = "127.0.0.1"
    port: int = 8000
    language: str | None = None
    config: str | None = None
    quantize: bool = False
    startup_timeout: float = 120.0
    existing_server_probe_timeout: float = 0.5
    title: str = "Pocket TTS"
    width: int = 1200
    height: int = 780
    min_width: int = 900
    min_height: int = 600


def find_available_port(host: str, requested_port: int) -> int:
    """Return requested_port when free, otherwise an OS-selected local port."""

    if requested_port != 0 and _can_bind(host, requested_port):
        return requested_port

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate_socket:
        candidate_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        candidate_socket.bind((host, 0))
        return int(candidate_socket.getsockname()[1])


def wait_for_health(health_url: str, timeout_seconds: float) -> bool:
    """Wait until the local FastAPI server responds to /health."""

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urlopen(health_url, timeout=0.5) as response:
                if response.status == 200:
                    return True
        except (OSError, URLError):
            time.sleep(0.1)

    return False


def import_webview() -> Any:
    try:
        import webview
    except ImportError as exc:
        raise RuntimeError(
            "Embedded desktop UI requires pywebview. Install Pocket TTS with the desktop "
            "extra: pip install 'pocket-tts[desktop]'."
        ) from exc

    return webview


def run_desktop_app(
    options: DesktopAppOptions,
    *,
    model_loader: Callable[..., Any] | None = None,
    config_factory: Callable[..., Any] | None = None,
    server_factory: Callable[..., Any] | None = None,
    webview_importer: Callable[[], Any] = import_webview,
    webview_module: Any | None = None,
    health_checker: Callable[[str, float], bool] = wait_for_health,
) -> str:
    """Start the local server and host it in an embedded desktop WebView."""

    import pocket_tts.main as main_module

    if options.port != 0:
        requested_url = f"http://{options.host}:{options.port}"
        if health_checker(f"{requested_url}/health", options.existing_server_probe_timeout):
            _open_desktop_window(requested_url, options, webview_importer, webview_module)
            return requested_url

    selected_port = find_available_port(options.host, options.port)
    app_url = f"http://{options.host}:{selected_port}"
    health_url = f"{app_url}/health"

    if model_loader is None:
        from pocket_tts.models.tts_model import TTSModel

        model_loader = TTSModel.load_model

    main_module.tts_model = model_loader(
        language=options.language, config=options.config, quantize=options.quantize
    )

    config_factory = config_factory or uvicorn.Config
    server_factory = server_factory or uvicorn.Server
    server = server_factory(
        config_factory(
            main_module.web_app,
            host=options.host,
            port=selected_port,
            log_level="warning",
            access_log=False,
        )
    )
    server_thread = threading.Thread(target=server.run, name="pocket-tts-server", daemon=True)
    server_thread.start()

    try:
        if not health_checker(health_url, options.startup_timeout):
            raise RuntimeError(f"Pocket TTS server did not become ready at {health_url}")

        _open_desktop_window(app_url, options, webview_importer, webview_module)
        return app_url
    finally:
        server.should_exit = True
        server_thread.join(timeout=5.0)


def _can_bind(host: str, port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe_socket:
            probe_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe_socket.bind((host, port))
    except OSError:
        return False

    return True


def _open_desktop_window(
    app_url: str,
    options: DesktopAppOptions,
    webview_importer: Callable[[], Any],
    webview_module: Any | None,
) -> None:
    if webview_module is None:
        webview_module = webview_importer()

    webview_module.create_window(
        options.title,
        app_url,
        width=options.width,
        height=options.height,
        min_size=(options.min_width, options.min_height),
        text_select=True,
    )
    logger.info("Opened Pocket TTS desktop app at %s", app_url)
    webview_module.start()

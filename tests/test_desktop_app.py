"""Tests for the standalone desktop app launcher."""

import socket
import types

from pocket_tts.desktop_app import DesktopAppOptions, find_available_port, run_desktop_app


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as free_socket:
        free_socket.bind(("127.0.0.1", 0))
        return free_socket.getsockname()[1]


def test_find_available_port_skips_busy_requested_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as busy_socket:
        busy_socket.bind(("127.0.0.1", 0))
        busy_socket.listen(1)
        busy_port = busy_socket.getsockname()[1]

        selected_port = find_available_port("127.0.0.1", busy_port)

    assert selected_port != busy_port


def test_run_desktop_app_embeds_local_server_and_stops_it_after_window_closes():
    events = []
    servers = []

    class FakeConfig:
        def __init__(self, app, host, port, log_level, access_log):
            self.app = app
            self.host = host
            self.port = port
            self.log_level = log_level
            self.access_log = access_log

    class FakeServer:
        def __init__(self, config):
            self.config = config
            self.should_exit = False
            servers.append(self)

        def run(self):
            events.append(("server_run", self.config.host, self.config.port))

    class FakeWebView:
        def create_window(self, title, url, **kwargs):
            events.append(("create_window", title, url, kwargs))
            return types.SimpleNamespace()

        def start(self):
            events.append(("webview_start",))

    def fake_model_loader(**kwargs):
        events.append(("load_model", kwargs))
        return types.SimpleNamespace(origin="english")

    def fake_health_checker(url, timeout_seconds):
        events.append(("health", url, timeout_seconds))
        return True

    app_url = run_desktop_app(
        DesktopAppOptions(host="127.0.0.1", port=0, language="english", startup_timeout=0.25),
        model_loader=fake_model_loader,
        config_factory=FakeConfig,
        server_factory=FakeServer,
        webview_module=FakeWebView(),
        health_checker=fake_health_checker,
    )

    assert app_url.startswith("http://127.0.0.1:")
    assert events[0] == ("load_model", {"language": "english", "config": None, "quantize": False})
    assert events[1] == ("server_run", "127.0.0.1", int(app_url.rsplit(":", maxsplit=1)[1]))
    assert servers[0].config.log_level == "warning"
    assert servers[0].config.access_log is False
    assert ("webview_start",) in events
    assert servers[0].should_exit is True

    create_window_events = [event for event in events if event[0] == "create_window"]
    assert create_window_events == [
        (
            "create_window",
            "Pocket TTS",
            app_url,
            {"width": 1200, "height": 780, "min_size": (900, 600), "text_select": True},
        )
    ]


def test_run_desktop_app_raises_when_embedded_webview_is_missing():
    class FakeConfig:
        def __init__(self, app, host, port, log_level, access_log):
            self.host = host
            self.port = port

    class FakeServer:
        def __init__(self, config):
            self.should_exit = False

        def run(self):
            return None

    def missing_webview_importer():
        raise RuntimeError("Install Pocket TTS with the desktop extra: pocket-tts[desktop]")

    try:
        run_desktop_app(
            DesktopAppOptions(host="127.0.0.1", port=0, startup_timeout=0.25),
            model_loader=lambda **kwargs: types.SimpleNamespace(origin="english"),
            config_factory=FakeConfig,
            server_factory=FakeServer,
            webview_importer=missing_webview_importer,
            health_checker=lambda url, timeout_seconds: True,
        )
    except RuntimeError as exc:
        assert "pocket-tts[desktop]" in str(exc)
    else:
        raise AssertionError("Expected missing embedded WebView dependency to raise RuntimeError")


def test_run_desktop_app_reuses_requested_port_when_server_is_already_ready():
    events = []

    class FakeWebView:
        def create_window(self, title, url, **kwargs):
            events.append(("create_window", title, url, kwargs))

        def start(self):
            events.append(("webview_start",))

    def fail_model_loader(**kwargs):
        raise AssertionError("Existing ready server should not load a second model")

    def fail_config_factory(**kwargs):
        raise AssertionError("Existing ready server should not create a Uvicorn config")

    def fake_health_checker(url, timeout_seconds):
        events.append(("health", url, timeout_seconds))
        return True

    app_url = run_desktop_app(
        DesktopAppOptions(host="127.0.0.1", port=8000, startup_timeout=0.25),
        model_loader=fail_model_loader,
        config_factory=fail_config_factory,
        webview_module=FakeWebView(),
        health_checker=fake_health_checker,
    )

    assert app_url == "http://127.0.0.1:8000"
    assert events == [
            ("health", "http://127.0.0.1:8000/health", 0.5),
        (
            "create_window",
            "Pocket TTS",
            "http://127.0.0.1:8000",
            {"width": 1200, "height": 780, "min_size": (900, 600), "text_select": True},
        ),
        ("webview_start",),
    ]


def test_run_desktop_app_uses_short_probe_before_starting_new_requested_port_server():
    events = []
    servers = []
    requested_port = get_free_port()

    class FakeConfig:
        def __init__(self, app, host, port, log_level, access_log):
            self.app = app
            self.host = host
            self.port = port
            self.log_level = log_level
            self.access_log = access_log

    class FakeServer:
        def __init__(self, config):
            self.config = config
            self.should_exit = False
            servers.append(self)

        def run(self):
            events.append(("server_run", self.config.host, self.config.port))

    class FakeWebView:
        def create_window(self, title, url, **kwargs):
            events.append(("create_window", title, url, kwargs))

        def start(self):
            events.append(("webview_start",))

    health_results = iter([False, True])

    def fake_health_checker(url, timeout_seconds):
        events.append(("health", url, timeout_seconds))
        return next(health_results)

    app_url = run_desktop_app(
        DesktopAppOptions(host="127.0.0.1", port=requested_port, startup_timeout=90.0),
        model_loader=lambda **kwargs: types.SimpleNamespace(origin="english"),
        config_factory=FakeConfig,
        server_factory=FakeServer,
        webview_module=FakeWebView(),
        health_checker=fake_health_checker,
    )

    assert app_url == f"http://127.0.0.1:{requested_port}"
    assert events[0] == ("health", f"http://127.0.0.1:{requested_port}/health", 0.5)
    assert ("server_run", "127.0.0.1", requested_port) in events
    assert ("health", f"http://127.0.0.1:{requested_port}/health", 90.0) in events
    assert servers[0].should_exit is True


def test_windows_app_entrypoint_uses_default_desktop_options(monkeypatch):
    import pocket_tts.windows_app as windows_app

    captured_options = []

    def fake_run_desktop_app(options):
        captured_options.append(options)
        return "http://127.0.0.1:8000"

    monkeypatch.setattr(windows_app, "run_desktop_app", fake_run_desktop_app)

    windows_app.main()

    assert captured_options == [DesktopAppOptions()]

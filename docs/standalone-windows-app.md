# Standalone Windows App

Pocket TTS can be packaged as a double-clickable Windows desktop app. The desktop app still uses the existing FastAPI server and HTML interface internally, but it displays the UI in an embedded WebView window instead of opening the user's default browser.

## Runtime Model

The app starts one local server on `127.0.0.1`. If a Pocket TTS server is already healthy on the requested port, the app reuses it instead of loading a second model. If the requested port is busy but not healthy, it selects another available local port and opens the embedded UI against that port.

The app shuts the server down when the desktop window closes.

Model weights, tokenizer files, and voice prompts are not bundled into the executable by default. They download on first use through the existing Hugging Face cache path and are reused on later launches.

## Development Run

```powershell
uv run --extra desktop pocket-tts app
```

## Windows Executable Build

Run this on Windows:

```powershell
.\scripts\build_windows_app.ps1
```

The build script:

1. Installs the `desktop` and `build-windows` extras.
2. Generates `build/windows/Pocket-TTS.ico`.
3. Runs PyInstaller in windowed mode.
4. Writes the packaged app under `dist/windows/`.
5. Resyncs the development environment with only the `desktop` extra so later app launches do not uninstall build-only packages.

## WebView Runtime

The embedded UI uses pywebview. On Windows, pywebview uses native Windows webview backends and supports Edge Chromium / WebView2. Microsoft documents WebView2 as the supported way to embed web technologies in native Windows desktop apps and documents separate WebView2 Runtime distribution options for shipped apps.

If a target machine does not have the WebView2 Runtime, distribute the Evergreen Runtime with the installer or document it as a prerequisite.

References:

- https://learn.microsoft.com/en-us/microsoft-edge/webview2/
- https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution
- https://pywebview.idepy.com/en/guide/installation
- https://pywebview.idepy.com/en/guide/freezing

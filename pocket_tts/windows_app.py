"""Windows desktop executable entry point."""

from pocket_tts.desktop_app import DesktopAppOptions, run_desktop_app


def main() -> None:
    run_desktop_app(DesktopAppOptions())


if __name__ == "__main__":
    main()

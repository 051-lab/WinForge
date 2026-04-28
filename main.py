"""WinForge v0.1.0 - Self-improving Windows desktop app."""
from loguru import logger
import sys


def main() -> None:
    """Application entry point."""
    logger.info("WinForge starting...")
    try:
        from app.window import WinForgeApp
        app = WinForgeApp()
        app.mainloop()
    except Exception as exc:  # pragma: no cover
        logger.exception("Fatal error: {}", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()

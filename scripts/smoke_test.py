"""Convenience wrapper for HTTP smoke tests."""

from app.main import main


if __name__ == "__main__":
    raise SystemExit(main(["smoke-test"]))

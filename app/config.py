"""Application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
TIMEZONE_NAME = "Asia/Ho_Chi_Minh"
VIETNAM_UTC_OFFSET = timezone(timedelta(hours=7), name="UTC+07:00")
REFERENCE_LONGITUDE_DEGREES = 105.0
NEW_MOON_EPOCH_JDE = 2451550.09765
SYNODIC_MONTH_DAYS = 29.530588853
SUPPORTED_START_DATE = "2000-01-01"
SUPPORTED_END_DATE = "2100-12-31"
MAX_RANGE_DAYS = 366
DEFAULT_STATIC_CACHE_SECONDS = 86400
ALGORITHM_VERSION = "meeus-v1"


def load_dotenv(path: Path | None = None) -> None:
    """Load a simple .env file without overriding existing environment variables."""

    dotenv_path = path or PROJECT_ROOT / ".env"
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        os.environ.setdefault(key, value)


load_dotenv()


def resolve_zoneinfo() -> timezone | ZoneInfo:
    """Return the preferred timezone object for Vietnam."""

    try:
        return ZoneInfo(TIMEZONE_NAME)
    except Exception:
        return VIETNAM_UTC_OFFSET


@dataclass(slots=True)
class Settings:
    """Runtime configuration derived from environment variables."""

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    data_dir: Path = DEFAULT_DATA_DIR
    timezone_name: str = TIMEZONE_NAME
    log_level: str = "INFO"
    static_cache_seconds: int = DEFAULT_STATIC_CACHE_SECONDS

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""

        return cls(
            app_host=os.getenv("APP_HOST", "0.0.0.0"),
            app_port=int(os.getenv("APP_PORT", "8000")),
            data_dir=Path(os.getenv("DATA_DIR", str(DEFAULT_DATA_DIR))),
            timezone_name=os.getenv("TZ", TIMEZONE_NAME),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            static_cache_seconds=int(
                os.getenv("STATIC_CACHE_SECONDS", str(DEFAULT_STATIC_CACHE_SECONDS))
            ),
        )

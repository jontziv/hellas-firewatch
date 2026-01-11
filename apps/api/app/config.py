from __future__ import annotations

from dataclasses import dataclass
import os


def _env(name: str, default: str) -> str:
    v = os.getenv(name)
    return v if v is not None and v != "" else default


@dataclass(frozen=True)
class Settings:
    db_url: str = _env("HF_DB_URL", "sqlite:///./var/app.db")
    rate_limit_per_minute: int = int(_env("HF_RATE_LIMIT_PER_MINUTE", "30"))
    verify_cooldown_seconds: int = int(_env("HF_VERIFY_COOLDOWN_SECONDS", "30"))

    dismiss_deny_threshold: int = int(_env("HF_DISMISS_DENY_THRESHOLD", "2"))
    dismiss_deny_over_confirm: bool = _env("HF_DISMISS_DENY_OVER_CONFIRM", "True").lower() in {
        "1", "true", "yes", "y"
    }

    save_photos: bool = _env("HF_SAVE_PHOTOS", "True").lower() in {"1", "true", "yes", "y"}
    photos_dir: str = _env("HF_PHOTOS_DIR", "./var/photos")


settings = Settings()

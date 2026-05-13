"""Centralized configuration. Reads from environment with sane defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
NOTES_FILE = DATA_DIR / "notes.json"


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    agent_max_steps: int


def load_settings() -> Settings:
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip(),
        agent_max_steps=int(os.getenv("AGENT_MAX_STEPS", "6")),
    )

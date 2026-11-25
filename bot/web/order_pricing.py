"""Shared browser/server work rates. Never trust client-supplied amounts."""
import json
from pathlib import Path


def installation_quote(config):
    if not isinstance(config, dict):
        raise ValueError("invalid_installation")
    rates_path = Path(__file__).resolve().parents[2] / "data" / "service-rates.js"
    rates = json.loads(rates_path.read_text(encoding="utf-8").split("=", 1)[1].strip().rstrip(";"))["video"]
    counts = {}
    for key in ("indoor", "outdoor"):
        value = config.get(key, 0)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
            raise ValueError("invalid_installation")
        counts[key] = value
    for key in ("nvr", "mobile"):
        if key in config and not isinstance(config[key], bool):
            raise ValueError("invalid_installation")
    total = 0
    for key, count in counts.items():
        tier = "one" if count == 1 else "two" if count == 2 else "threeToEight" if count <= 8 else "overEight"
        total += count * rates[key + "Camera"][tier]
    if sum(counts.values()):
        total += rates["recorderSetup"] if config.get("nvr") else 0
        total += rates["mobileAppSetup"] if config.get("mobile") else 0
    return {**counts, "nvr": config.get("nvr", False), "mobile": config.get("mobile", False)}, total

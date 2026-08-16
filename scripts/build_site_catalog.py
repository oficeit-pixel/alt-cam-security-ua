import json
from pathlib import Path

from catalog_rules import load_public_products


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "catalog-sync" / "output" / "normalized"
OUTPUT = ROOT / "catalog-data.js"

products = load_public_products(SOURCE)

payload = "window.ALTCAM_CATALOG = " + json.dumps(products, ensure_ascii=False, indent=2) + ";\n"
OUTPUT.write_text(payload, encoding="utf-8")
print(f"Created {OUTPUT.name}: {len(products)} products")

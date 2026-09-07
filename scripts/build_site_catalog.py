import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "catalog-sync" / "output" / "storefront-approval.json"
OUTPUT = ROOT / "catalog-data.js"

products = json.loads(SOURCE.read_text(encoding="utf-8"))

payload = "window.ALTCAM_CATALOG = " + json.dumps(products, ensure_ascii=False, indent=2) + ";\n"
OUTPUT.write_text(payload, encoding="utf-8")
print(f"Created {OUTPUT.name}: {len(products)} products")

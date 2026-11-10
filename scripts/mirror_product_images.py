"""Manual supplier-image migration. Default mode is read-only and offline."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://alt-cam.net.ua"
HOSTS = {"viatec.ua", "b2b.yugtorg.com"}
MAX_BYTES = 15 * 1024 * 1024


def allowed(url):
    try:
        parsed = urllib.parse.urlsplit(url)
        return (parsed.scheme == "https" and parsed.hostname in HOSTS
                and not parsed.username and not parsed.password
                and parsed.port in (None, 443))
    except (ValueError, TypeError):
        return False


def read_catalog(raw):
    match = re.fullmatch(r"\s*window\.ALTCAM_CATALOG\s*=\s*([\s\S]*?)\s*;?\s*", raw)
    if not match:
        raise ValueError("Unexpected catalog format")
    data = json.loads(match[1])
    if not isinstance(data, list):
        raise ValueError("Catalog must be an array")
    return data


def inventory(products):
    result = {}
    for product in products:
        for url in [product.get("image"), *(product.get("images") or [])]:
            if isinstance(url, str) and allowed(url):
                result.setdefault(url, set()).add(str(product["id"]))
    return {url: sorted(ids) for url, ids in sorted(result.items())}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    # Do not follow supplier redirects to arbitrary hosts or private services.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def download(url):
    if not allowed(url):
        raise ValueError("Source host is not allowed")
    request = urllib.request.Request(url, headers={"User-Agent": "ALT-CAM-Image-Mirror/1.0"})
    with urllib.request.build_opener(NoRedirect).open(request, timeout=30) as response:
        if not response.headers.get("Content-Type", "").lower().startswith("image/"):
            raise ValueError("Response is not an image")
        content = response.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise ValueError("Image exceeds 15 MiB")
    return content


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def convert(content, url):
    from PIL import Image, ImageOps
    Image.MAX_IMAGE_PIXELS = 40_000_000
    with Image.open(io.BytesIO(content)) as source:
        if source.width * source.height > Image.MAX_IMAGE_PIXELS:
            raise ValueError("Image dimensions exceed safety limit")
        if getattr(source, "n_frames", 1) > 1:
            raise ValueError("Animated image requires manual review")
        picture = ImageOps.exif_transpose(source).convert("RGBA")
    folder = ROOT / "assets/products" / hashlib.sha256(url.encode()).hexdigest()[:24]
    variants = []
    for width in (480, 800, 1200):
        image = picture.copy()
        # No upscaling; preserve the whole product and its aspect ratio.
        if image.width > width:
            image = image.resize((width, max(1, round(image.height * width / image.width))), Image.Resampling.LANCZOS)
        if variants and variants[-1]["width"] == image.width:
            continue
        buffer = io.BytesIO()
        image.save(buffer, format="WEBP", quality=85, method=6)
        target = folder / (str(image.width) + ".webp")
        atomic_write(target, buffer.getvalue())
        variants.append({"url": ORIGIN + "/" + target.relative_to(ROOT).as_posix(),
                         "width": image.width, "height": image.height})
    return {"sha256": hashlib.sha256(content).hexdigest(), "variants": variants,
            "url": variants[-1]["url"]}


def replace_images(products, manifest):
    for product in products:
        original = [product.get("image"), *(product.get("images") or [])]
        product["image_metadata"] = {
            url: manifest[url] for url in dict.fromkeys(original)
            if url in manifest and manifest[url].get("url")
        }
        def replace(url):
            return manifest.get(url, {}).get("url", url)
        if product.get("image"):
            product["image"] = replace(product["image"])
        if isinstance(product.get("images"), list):
            product["images"] = [replace(url) for url in product["images"]]
    return products


def verified(entry):
    if entry.get("status") != "ok" or not entry.get("variants"):
        return False
    for variant in entry["variants"]:
        url = variant.get("url", "")
        if not url.startswith(ORIGIN + "/assets/products/"):
            return False
        target = (ROOT / url[len(ORIGIN) + 1:]).resolve()
        if not target.is_relative_to((ROOT / "assets/products").resolve()) or not target.is_file():
            return False
    return entry.get("url") == entry["variants"][-1]["url"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--rights-confirmed", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Replace successful URLs in catalog-data.js")
    parser.add_argument("--limit", type=int, default=20, help="Maximum unique downloads; default pilot: 20")
    args = parser.parse_args(argv)
    if args.apply and not args.download:
        parser.error("--apply requires --download")
    if args.download and not args.rights_confirmed:
        parser.error("Owner must confirm photo usage rights with --rights-confirmed")
    if args.limit < 1:
        parser.error("--limit must be positive")
    catalog = ROOT / "catalog-data.js"
    original = catalog.read_bytes()
    products = read_catalog(original.decode("utf-8-sig"))
    urls = inventory(products)
    if not args.download:
        print(json.dumps({"mode": "offline-dry-run", "unique": len(urls), "urls": urls}, ensure_ascii=False, indent=2))
        return
    try:
        import PIL  # noqa: F401
    except ImportError:
        parser.error("Install optional tooling: python -m pip install Pillow")
    report_path = ROOT / "output/product-images/manifest.json"
    manifest = json.loads(report_path.read_text("utf-8")) if report_path.exists() else {}
    pending = [(url, ids) for url, ids in urls.items() if not verified(manifest.get(url, {}))]
    for url, ids in pending[:args.limit]:
        for attempt in range(3):
            try:
                manifest[url] = {**convert(download(url), url), "product_ids": ids, "status": "ok"}
                break
            except Exception as error:
                if attempt == 2:
                    # Do not print remote response bodies or embed failures into public URLs.
                    manifest[url] = {"status": "error", "error_type": type(error).__name__, "product_ids": ids}
                else:
                    time.sleep(2 ** attempt)
        atomic_write(report_path, json.dumps(manifest, ensure_ascii=False, indent=2).encode())
        time.sleep(0.3)
    if args.apply:
        if catalog.read_bytes() != original:
            raise RuntimeError("Catalog changed during download; refusing to overwrite")
        backup = ROOT / "output/product-images" / (hashlib.sha256(original).hexdigest() + ".catalog-backup.js")
        if not backup.exists():
            atomic_write(backup, original)
        result = replace_images(products, {url: entry for url, entry in manifest.items() if verified(entry)})
        atomic_write(catalog, ("window.ALTCAM_CATALOG=" + json.dumps(result, ensure_ascii=False) + ";\n").encode())
    print(json.dumps({"manifest": str(report_path), "catalog_changed": args.apply,
                      "success": sum(v.get("status") == "ok" for v in manifest.values())}))


if __name__ == "__main__":
    main()

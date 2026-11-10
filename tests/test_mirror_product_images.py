import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("mirror", Path(__file__).parents[1] / "scripts/mirror_product_images.py")
mirror = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mirror)


class MirrorTests(unittest.TestCase):
    def test_host_allowlist(self):
        self.assertTrue(mirror.allowed("https://viatec.ua/upload/photo.jpg"))
        for url in ["http://viatec.ua/x", "https://viatec.ua.evil.test/x",
                    "https://user:pass@viatec.ua/x", "https://127.0.0.1/x",
                    "https://viatec.ua:8443/x", "file:///x"]:
            self.assertFalse(mirror.allowed(url))

    def test_catalog_is_json_not_executed(self):
        self.assertEqual(mirror.read_catalog('window.ALTCAM_CATALOG=[{"id":"a"}];'), [{"id": "a"}])
        with self.assertRaises((ValueError, json.JSONDecodeError)):
            mirror.read_catalog("window.ALTCAM_CATALOG=alert(1);")

    def test_dedup_and_success_only(self):
        url = "https://viatec.ua/upload/a.jpg"
        failed = "https://b2b.yugtorg.com/b.png"
        products = [{"id": "a", "image": url, "images": [url, failed]}, {"id": "b", "image": url}]
        self.assertEqual(mirror.inventory(products)[url], ["a", "b"])
        manifest = {url: {"url": "https://alt-cam.net.ua/assets/products/hash/480.webp"},
                    failed: {"status": "error"}}
        result = mirror.replace_images(products, manifest)
        self.assertEqual(result[0]["image"], manifest[url]["url"])
        self.assertEqual(result[0]["images"][1], failed)
        self.assertEqual(result[0]["id"], "a")

    def test_missing_files_never_verified(self):
        self.assertFalse(mirror.verified({"status": "ok", "url": "https://evil.test/a",
                                         "variants": [{"url": "https://evil.test/a"}]}))


if __name__ == "__main__":
    unittest.main()

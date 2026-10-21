import contextlib
import importlib.util
import io
import os
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("publisher", Path(__file__).with_name("publish_due.py"))
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class PublisherRegressionTests(unittest.TestCase):
    def test_force_never_republishes_success_or_disabled_platforms(self):
        post = {"id": "mixed", "platforms": ["instagram", "telegram", "tiktok", "instagram_story"],
                "caption": "text", "status": "approved", "scheduled_at": "2026-01-01T00:00:00Z"}
        state = {"published": {"mixed": {"instagram": {"published_at": "2026-01-01T00:00:00Z"}}}}
        output = io.StringIO()
        with patch.object(publisher, "load_json", side_effect=lambda path, default: {"posts": [post]} if path == publisher.POSTS_FILE else state), \
             patch.object(publisher, "load_env_file"), \
             patch.object(publisher, "platform_has_credentials", return_value=True), \
             patch.dict(os.environ, {"DRY_RUN": "true", "DISABLED_PLATFORMS": "tiktok,instagram_story", "MIN_SUCCESS_INTERVAL_MINUTES": "0"}), \
             patch("sys.argv", ["publish_due.py", "--dry-run", "--force"]), contextlib.redirect_stdout(output):
            self.assertEqual(publisher.main(), 0)
        self.assertIn("DRY PUBLISH mixed -> telegram", output.getvalue())
        for platform in ["instagram", "tiktok", "instagram_story"]:
            self.assertNotIn(f"DRY PUBLISH mixed -> {platform}", output.getvalue())

    def test_cloud_workflow_disables_legacy_routes(self):
        workflow = (Path(__file__).resolve().parents[2] / ".github/workflows/social-publisher.yml").read_text(encoding="utf-8")
        self.assertIn('DISABLED_PLATFORMS: "facebook,facebook_story,instagram_story,tiktok"', workflow)
        self.assertNotIn('          - tiktok', workflow)
        self.assertNotIn('          - instagram_story', workflow)

    def test_threads_keeps_complete_cta_with_long_tracking_link(self):
        text = "Камери для вашого будинку. " * 40 + "\nhttps://t.me/alt_cam_bot\nhttps://alt-cam.net.ua/catalog.html?utm_content=" + "x" * 180
        result = publisher.caption_for({"caption": text}, "threads")
        self.assertLessEqual(len(result.encode("utf-16-le")) // 2, 500)
        self.assertTrue(result.endswith("https://t.me/alt_cam_bot"))
        self.assertTrue(result.startswith("Камери для вашого будинку."))

    def test_threads_emoji_and_short_copy(self):
        text = "📷 " * 230 + "https://alt-cam.net.ua"
        self.assertLessEqual(len(publisher.threads_caption(text).encode("utf-16-le")) // 2, 500)
        self.assertEqual(publisher.threads_caption("Короткий допис"), "Короткий допис")

    def test_threads_backlog_does_not_starve_other_networks(self):
        posts = [{"id": f"old-{i}", "platforms": ["threads"], "caption": "text",
                  "status": "approved", "scheduled_at": "2026-01-01T00:00:00Z"} for i in range(5)]
        posts.append({"id": "new", "platforms": ["instagram", "telegram"], "caption": "text",
                      "status": "approved", "scheduled_at": "2026-01-02T00:00:00Z"})
        state = {"published": {}}
        def load(path, default):
            return {"posts": posts} if path == publisher.POSTS_FILE else state
        output = io.StringIO()
        with patch.object(publisher, "load_json", side_effect=load), \
             patch.object(publisher, "load_env_file"), \
             patch.object(publisher, "platform_has_credentials", return_value=True), \
             patch.dict(os.environ, {"MAX_POSTS_PER_RUN": "3", "MIN_SUCCESS_INTERVAL_MINUTES": "0",
                                     "DRY_RUN": "true", "DISABLED_PLATFORMS": ""}), \
             patch("sys.argv", ["publish_due.py", "--dry-run"]), contextlib.redirect_stdout(output):
            self.assertEqual(publisher.main(), 0)
        self.assertIn("DRY PUBLISH new -> instagram", output.getvalue())
        self.assertIn("DRY PUBLISH new -> telegram", output.getvalue())
        self.assertEqual(output.getvalue().count("-> threads"), 1)


if __name__ == "__main__":
    unittest.main()

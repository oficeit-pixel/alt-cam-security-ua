import importlib.util
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('seo_check',Path(__file__).parents[1]/'scripts/seo-check.py')
seo=importlib.util.module_from_spec(spec);spec.loader.exec_module(seo)
class Check(unittest.TestCase):
    def test_parser_and_findings(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: https://alt-cam.net.ua/sitemap.xml')
            (root/'sitemap.xml').write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://alt-cam.net.ua/</loc></url></urlset>')
            page='<html><head><title>Test</title><meta name="description" content="Description"><link rel="canonical" href="https://alt-cam.net.ua/"><script type="application/ld+json">{"@type":"LocalBusiness"}</script></head><body><h1>Heading</h1><h2>Section</h2></body></html>'
            (root/'index.html').write_text(page)
            self.assertEqual(seo.audit(root)['issues'],[])
            (root/'index.html').write_text(page.replace('</body>','<nav><a href="#">Bad</a><a href="/missing/">Missing</a></nav><img src="x"><h4>Skipped</h4></body>'))
            kinds=seo.audit(root)['counts']
            for name in ['navigation_hash','broken_link','empty_alt','heading_jump']: self.assertIn(name,kinds)
    def test_invalid_xml(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'sitemap.xml').write_text('<broken>')
            self.assertIn('invalid_sitemap',seo.audit(d)['counts'])
if __name__=='__main__': unittest.main()

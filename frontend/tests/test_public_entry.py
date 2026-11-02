"""Dependency-free public entry checks; JavaScript checks use macOS JavaScriptCore."""
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from urllib.parse import unquote, urlsplit
import zipfile


FRONTEND = Path(__file__).resolve().parents[1]
JSC = shutil.which("osascript")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.scripts = []
        self.inline = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])
        if tag == "script":
            self.inline = "src" not in attrs and attrs.get("type", "") not in (
                "application/ld+json", "application/json",
            )

    def handle_data(self, data):
        if self.inline:
            self.scripts.append(data)

    def handle_endtag(self, tag):
        if tag == "script":
            self.inline = False


def javascript(source):
    result = subprocess.run(
        [JSC, "-l", "JavaScript", "-e", source],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def install_suggestion(**options):
    source = (FRONTEND / "assets/mobile-install.js").read_text()
    return javascript("""
      const options = OPTIONS;
      const nodes = [], warnings = [], stored = {};
      if (options.dismissed) stored['rightconnect-install-dismissed'] = '1';
      function node(tag) {
        const n = {tag, children:[], handlers:{}, removed:false,
          append(...children) { this.children.push(...children); },
          prepend(child) { this.children.unshift(child); },
          setAttribute(key, value) { this[key] = value; },
          addEventListener(key, handler) { this.handlers[key] = handler; },
          remove() { this.removed = true; }};
        nodes.push(n);
        return n;
      }
      const host = options.marketplace ? node('main') : null;
      const document = {referrer:options.referrer || '', head:node('head'), body:node('body'), createElement:node, querySelector:() => host};
      const storage = {
        getItem(key) { if(options.storageBlocked) throw new Error('blocked'); return stored[key] || null; },
        setItem(key, value) { if(options.storageBlocked) throw new Error('blocked'); stored[key] = value; }
      };
      const execute = new Function('navigator','matchMedia','document','localStorage','console', SOURCE);
      const navigator = {userAgent:options.ua || '', platform:options.platform || '', maxTouchPoints:options.touch || 0, standalone:options.iosStandalone || false};
      const run = () => execute(navigator, () => ({matches:!!options.standalone}), document, storage, {warn:message => warnings.push(message)});
      run();
      const banner = nodes.find(n => n.tag === 'aside');
      const action = nodes.find(n => n.tag === 'a');
      if(options.close && banner) banner.children.find(n => n.tag === 'button').handlers.click();
      if(options.close) run();
      JSON.stringify({
        banners:nodes.filter(n => n.tag === 'aside' && !n.removed).length,
        href:action ? action.href : null,
        download:action ? action.download || null : null,
        lang:banner ? banner.lang : null,
        warnings:warnings.length,
        dismissed:stored['rightconnect-install-dismissed'] === '1',
        inMarketplace:!!host && host.children.includes(banner)
      });
    """.replace("OPTIONS", json.dumps(options)).replace("SOURCE", json.dumps(source)))


class PublicEntryTests(unittest.TestCase):
    def test_homepage_destinations_exist(self):
        parser = PageParser()
        parser.feed((FRONTEND / "index.html").read_text())
        self.assertIn("/pages/marketplace.html", parser.links)
        self.assertIn("/pages/auth.html", parser.links)
        self.assertIn("/pages/auth.html#sign-in", parser.links)
        self.assertIn("/downloads/rightconnect.apk", parser.links)
        for href in parser.links:
            path = unquote(urlsplit(href).path)
            if path.startswith("/") and path != "/":
                self.assertTrue((FRONTEND / path.lstrip("/")).is_file(), href)

    def test_all_public_pages_include_suggestion(self):
        for page in [FRONTEND / "index.html", *FRONTEND.glob("pages/*.html")]:
            with self.subTest(page=page.name):
                self.assertIn("mobile-install.js", page.read_text())

    def test_apk_is_packaged_android_app(self):
        with zipfile.ZipFile(FRONTEND / "downloads/rightconnect.apk") as apk:
            self.assertIn("AndroidManifest.xml", apk.namelist())
            self.assertIn("classes.dex", apk.namelist())
            self.assertIsNone(apk.testzip())

    def test_public_download_and_role_tours_are_wired(self):
        page = (FRONTEND / "pages/marketplace.html").read_text()
        for view in ["app-download", "app-tour"]:
            self.assertIn(f'data-view="{view}"', page)
            self.assertIn(f'class="view" id="{view}"', page)
        for role in ["customer", "expert", "company"]:
            self.assertIn(f'data-start-tour="{role}"', page)
        parser = PageParser()
        parser.feed(page)
        self.assertIn("/downloads/rightconnect.apk", parser.links)
        self.assertIn("../assets/app-tour.js", page)
        self.assertIn("/assets/app-tour.js", (FRONTEND / "sw.js").read_text())

    def test_manifest_keeps_app_launch_destination_without_play_link(self):
        manifest = json.loads((FRONTEND / "manifest.webmanifest").read_text())
        self.assertEqual(manifest["start_url"], "/pages/marketplace.html")
        self.assertEqual(manifest["related_applications"], [])

    @unittest.skipUnless(JSC, "JavaScriptCore validation requires macOS osascript")
    def test_javascript_syntax(self):
        scripts = []
        for page in [FRONTEND / "index.html", *FRONTEND.glob("pages/*.html")]:
            parser = PageParser()
            parser.feed(page.read_text())
            scripts.extend(parser.scripts)
        scripts.extend(path.read_text() for path in [
            FRONTEND / "assets/mobile-install.js", FRONTEND / "sw.js",
            FRONTEND / "assets/showcases.js", FRONTEND / "assets/workspace.js",
            FRONTEND / "assets/app-tour.js",
        ])
        self.assertTrue(javascript(
            "const scripts = " + json.dumps(scripts) +
            "; scripts.forEach(source => new Function(source)); JSON.stringify(true);"
        ))

    @unittest.skipUnless(JSC, "JavaScriptCore validation requires macOS osascript")
    def test_platform_detection(self):
        for options, banners, href in [
            ({"ua": "Android Chrome Mobile"}, 1, "/downloads/rightconnect.apk"),
            ({"ua": "iPhone Safari"}, 1, "/#iphone-install"),
            ({"ua": "Desktop", "platform": "MacIntel", "touch": 5}, 1, "/#iphone-install"),
            ({"ua": "Desktop"}, 0, None),
            ({"ua": "Android median"}, 0, None),
            ({"ua": "Android; wv)"}, 0, None),
            ({"ua": "Android", "standalone": True}, 0, None),
            ({"ua": "iPhone", "iosStandalone": True}, 0, None),
            ({"ua": "Android", "referrer": "android-app://app.rightconnect.twa"}, 0, None),
            ({"ua": "Android", "dismissed": True}, 0, None),
        ]:
            with self.subTest(options=options):
                result = install_suggestion(**options)
                self.assertEqual(result["banners"], banners)
                self.assertEqual(result["href"], href)
                if banners:
                    self.assertEqual(result["lang"], "en")
                    self.assertEqual(result["download"], "RightConnect.apk" if "Android" in options["ua"] else None)

    @unittest.skipUnless(JSC, "JavaScriptCore validation requires macOS osascript")
    def test_dismissal_survives_navigation(self):
        result = install_suggestion(ua="Android", close=True)
        self.assertTrue(result["dismissed"])
        self.assertEqual(result["banners"], 0)

    @unittest.skipUnless(JSC, "JavaScriptCore validation requires macOS osascript")
    def test_blocked_storage_does_not_break_browsing(self):
        result = install_suggestion(ua="Android", storageBlocked=True)
        self.assertEqual(result["banners"], 1)
        self.assertGreater(result["warnings"], 0)

    @unittest.skipUnless(JSC, "JavaScriptCore validation requires macOS osascript")
    def test_marketplace_banner_stays_out_of_fixed_sidebar(self):
        result = install_suggestion(ua="Android", marketplace=True)
        self.assertTrue(result["inMarketplace"])


if __name__ == "__main__":
    unittest.main()

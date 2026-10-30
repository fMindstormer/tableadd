"""Screenshot the demo page's table for the README, in Chromium: python tools/picture.py 11 6 4

The page loads IBM Plex from Google Fonts. Where that is out of reach, point PLEX_FONTS at a folder holding the
fonts' .woff2 files (npm install @ibm/plex-sans @ibm/plex-sans-condensed @ibm/plex-mono) and they are used
instead; otherwise the picture falls back to the system's fonts."""
import base64
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FACES = [("IBM Plex Sans", 400, "IBMPlexSans-Regular"), ("IBM Plex Sans", 600, "IBMPlexSans-SemiBold"),
         ("IBM Plex Sans Condensed", 600, "IBMPlexSansCondensed-SemiBold"),
         ("IBM Plex Sans Condensed", 700, "IBMPlexSansCondensed-Bold"),
         ("IBM Plex Mono", 400, "IBMPlexMono-Regular"), ("IBM Plex Mono", 600, "IBMPlexMono-SemiBold")]


def local_fonts():
    folder = os.environ.get("PLEX_FONTS")
    if not folder:
        return ""
    files = {p.stem: p for p in Path(folder).rglob("*.woff2")}
    rules = []
    for family, weight, stem in FACES:
        if stem in files:
            data = base64.b64encode(files[stem].read_bytes()).decode()
            rules.append(f"@font-face{{font-family:'{family}';font-weight:{weight};font-style:normal;"
                         f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return "".join(rules)


def main(a=11, b=6, bits=4, out=ROOT / "docs" / "example.png"):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1800, "height": 1000}, device_scale_factor=2)
        page.goto((ROOT / "docs" / "index.html").as_uri())
        page.add_style_tag(content=local_fonts() + "main{max-width:none}.scroller{overflow:visible}")
        page.select_option("#bits", str(bits))
        page.fill("#a", str(a))
        page.fill("#b", str(b))
        page.evaluate("document.activeElement.blur()")           # no focus ring in the picture
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(300)
        box = page.evaluate("""() => {
            const r = document.querySelector('.readout').getBoundingClientRect(),
                  v = document.querySelector('#verdict').getBoundingClientRect(),
                  t = document.querySelector('table.adder').getBoundingClientRect(),
                  x = Math.min(r.x, t.x) - 14;
            return [x, r.y - 14, Math.max(v.right, t.right) - x + 14, t.bottom - r.y + 28]; }""")
        page.screenshot(path=str(out), clip=dict(zip(("x", "y", "width", "height"), box)))
        print(page.text_content("#eq"), "|", page.text_content("#verdict"), "|", out)
        browser.close()


if __name__ == "__main__":
    main(*[int(v) for v in sys.argv[1:4]])

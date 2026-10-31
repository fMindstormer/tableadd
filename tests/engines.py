"""Lay the adder tables out in real engines and compare every cell's column with the specification.

  chromium    Blink, the engine in Chrome and Edge (via Playwright)
  firefox     Gecko, in the Firefox app on macOS: a tab opens a page served from 127.0.0.1 and posts the layout back
  safari      WebKit, in the Safari app on macOS, the same way
  webkitgtk   WebKit, the engine Safari is built on, in its Linux port (via webkitgtk_layout.py)
  weasyprint  WeasyPrint's own table layout, in Python (cells carry their grid column)
  qtwebkit    the 2016 WebKit inside wkhtmltopdf: a script in the page measures the cells, pdftotext reads them

python tests/engines.py BITS [SAMPLE]: every BITS-bit sum (BITS <= 4) or SAMPLE random ones, in every engine
installed here; engines that are missing are skipped.
"""
import os
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tableadd import decode, rows  # noqa: E402
from tableadd.adder import bits  # noqa: E402
from tableadd.html import table  # noqa: E402
from tableadd.table import lay_out  # noqa: E402

PITCH = 10
CSS = (f"<style>table{{border-collapse:collapse;border-spacing:0;margin:2px}}td{{width:{PITCH}px;"
       f"min-width:{PITCH}px;max-width:{PITCH}px;height:{PITCH}px;padding:0;border:0}}</style>")


def cases(n, sample=None, seed=0):
    allc = [(x, y, c) for x in range(2 ** n) for y in range(2 ** n) for c in (0, 1)] if n <= 4 else None
    if allc is not None and not sample:
        return allc
    rng = random.Random(seed)
    return [(rng.randrange(2 ** n), rng.randrange(2 ** n), rng.randrange(2)) for _ in range(sample or 100)]


def check(name, n, got_layouts, batch):
    """Compare engine layouts (list of per-row column lists) with the spec; return (mismatched, wrong sums)."""
    mism = wrong = 0
    for (x, y, c), got in zip(batch, got_layouts):
        a, b = bits(x, n), bits(y, n)
        want = lay_out(rows(a, b, c))
        if got != want:
            mism += 1
        elif decode(a, b, c, got) != x + y + c:
            wrong += 1
    return mism, wrong


def chromium(n=4, sample=None):
    from playwright.sync_api import sync_playwright
    batch_all = cases(n, sample)
    mism = wrong = 0
    with sync_playwright() as p:
        br = p.chromium.launch()
        page = br.new_page(viewport={"width": 1600, "height": 900})
        for k in range(0, len(batch_all), 64):
            batch = batch_all[k:k + 64]
            page.set_content(CSS + "".join(table(x, y, n, c, tid=f"t{j}") for j, (x, y, c) in enumerate(batch)))
            got = page.evaluate("""ids => ids.map(id => { const t = document.getElementById(id), L = t.getBoundingClientRect().left;
                return [...t.rows].map(r => [...r.cells].map(c => Math.round((c.getBoundingClientRect().left - L) / %d))); })""" % PITCH,
                                [f"t{j}" for j in range(len(batch))])
            m, w = check("chromium", n, got, batch)
            mism += m; wrong += w
        version = br.version
        br.close()
    return f"Chromium {version}", len(batch_all), mism, wrong


PAGE = """<!doctype html><html><head><meta charset="utf-8">%s<style>#box{width:40000px}</style></head><body>
<p id="st">laying out...</p><div id="box"></div><script>
const box = document.getElementById("box"), out = [];
for (const html of %s) {
  box.innerHTML = html;
  out.push([...box.querySelectorAll("table")].map(t => { const L = t.getBoundingClientRect().left;
    return [...t.rows].map(r => [...r.cells].map(c => Math.round((c.getBoundingClientRect().left - L) / %d))); }));
}
box.innerHTML = "";
fetch("/", {method: "POST", body: JSON.stringify(out)})
  .then(() => document.getElementById("st").textContent = "done, the layout was sent back; you can close this tab");
</script></body></html>"""


def desktop(app):
    """A browser app installed on macOS. It opens a tab on a page served from 127.0.0.1, which lays the tables
    out and posts back the column of every cell."""
    def run(n=4, sample=None):
        if sys.platform != "darwin" or not Path(f"/Applications/{app}.app").exists():
            raise RuntimeError(f"needs {app} in /Applications (macOS)")
        import json
        import threading
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        batch_all = cases(n, sample)
        batches = [batch_all[k:k + 64] for k in range(0, len(batch_all), 64)]
        html = ["".join(table(x, y, n, c) for x, y, c in batch) for batch in batches]
        body = (PAGE % (CSS, json.dumps(html), PITCH)).encode()
        loaded, posted, got = threading.Event(), threading.Event(), []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                if self.path != "/":                             # the favicon
                    self.send_response(404); self.end_headers(); return
                loaded.set()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                got[:] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                self.send_response(204); self.end_headers()
                posted.set()

        srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_address[1]}/"
        try:
            for _ in range(3):                                   # an app that is starting can drop the URL
                subprocess.run(["open", "-a", app, url], check=True)
                if loaded.wait(30):
                    break
            if not posted.wait(300):
                raise RuntimeError(f"{app} sent no layout back")
        finally:
            srv.shutdown()
        if len(got) != len(batches):
            raise RuntimeError(f"{app} sent back {len(got)} of {len(batches)} batches")
        mism = wrong = 0
        for batch, layouts in zip(batches, got):
            m, w = check(app.lower(), n, layouts, batch)
            mism += m; wrong += w
        version = subprocess.run(["defaults", "read", f"/Applications/{app}.app/Contents/Info.plist",
                                  "CFBundleShortVersionString"], capture_output=True, text=True).stdout.strip()
        return f"{app} {version}", len(batch_all), mism, wrong
    return run


def weasyprint_engine(n=4, sample=None):
    import logging
    for lg in ("weasyprint", "fontTools"):
        logging.getLogger(lg).setLevel(logging.ERROR)
    import weasyprint
    from weasyprint.formatting_structure import boxes
    batch_all = cases(n, sample)
    mism = wrong = 0
    for k in range(0, len(batch_all), 32):
        batch = batch_all[k:k + 32]
        html = "<style>@page{size:4000px 6000px}</style>" + CSS + "".join(table(x, y, n, c) for x, y, c in batch)
        doc = weasyprint.HTML(string=html).render()
        tables = []

        def walk(bx):
            if isinstance(bx, boxes.TableBox):
                tables.append([[cell.grid_x for cell in row.children] for g in bx.children for row in g.children])
                return
            for ch in getattr(bx, "children", None) or []:
                walk(ch)
        for pg in doc.pages:
            walk(pg._page_box)
        m, w = check("weasyprint", n, tables, batch)
        mism += m; wrong += w
    return f"WeasyPrint {weasyprint.__version__}", len(batch_all), mism, wrong


SCRIPT = """<script>window.onload = function () { var out = [], ts = document.getElementsByTagName('table');
for (var t = 0; t < ts.length; t++) { var T = ts[t], rs = [];
  for (var r = 0; r < T.rows.length; r++) { var cs = [];
    for (var c = 0; c < T.rows[r].cells.length; c++) cs.push(Math.round(T.rows[r].cells[c].offsetLeft / %d));
    rs.push(cs.join(',')); }
  out.push('T' + t + ':' + rs.join(';')); }
document.body.innerHTML = '<div style="font:7px monospace;width:40000px;white-space:pre">' + out.join('\\n') + '</div>'; };</script>""" % PITCH


def qtwebkit(n=4, sample=None):
    batch_all = cases(n, sample)
    mism = wrong = 0
    tmp = tempfile.mkdtemp()
    for k in range(0, len(batch_all), 64):
        batch = batch_all[k:k + 64]
        src, pdf = os.path.join(tmp, "t.html"), os.path.join(tmp, "t.pdf")
        Path(src).write_text("<!doctype html><html><head>" + CSS + SCRIPT + "</head><body>" +
                             "".join(table(x, y, n, c) for x, y, c in batch) + "</body></html>")
        subprocess.run(["wkhtmltopdf", "-q", "--page-width", "3000mm", "--page-height", "3000mm",
                        "--javascript-delay", "300", src, pdf], capture_output=True, timeout=180)
        text = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout
        got = {}
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("T") and ":" in line:
                tid, rest = line.split(":", 1)
                rws = [[int(v) for v in r.split(",") if v] for r in rest.split(";")]
                x0 = rws[0][0]
                got[int(tid[1:])] = [[v - x0 for v in r] for r in rws]
        m, w = check("qtwebkit", n, [got.get(j) for j in range(len(batch))], batch)
        mism += m; wrong += w
    ver = subprocess.run(["wkhtmltopdf", "--version"], capture_output=True, text=True).stdout.strip()
    return f"QtWebKit ({ver})", len(batch_all), mism, wrong


def gi_python():
    """A Python that has PyGObject and WebKitGTK (the system one, usually), or None."""
    probe = "import gi; gi.require_version('WebKit2', '4.1'); from gi.repository import WebKit2"
    for exe in (os.environ.get("WEBKITGTK_PYTHON"), "/usr/bin/python3", "python3", "python3.12"):
        if exe and shutil.which(exe) and subprocess.run([exe, "-c", probe], capture_output=True).returncode == 0:
            return exe
    return None


def webkitgtk(n=4, sample=None):
    """WebKitGTK, the Linux port of WebKit (the engine Safari is built on), driven by webkitgtk_layout.py."""
    exe = gi_python()
    if not (exe and shutil.which("xvfb-run")):
        raise RuntimeError("needs WebKitGTK with PyGObject (Ubuntu: gir1.2-webkit2-4.1) and xvfb-run")
    helper = Path(__file__).resolve().parent / "webkitgtk_layout.py"
    batch_all = cases(n, sample)
    mism = wrong = 0
    version = "?"
    with tempfile.TemporaryDirectory() as tmp:
        for k in range(0, len(batch_all), 128):
            batch = batch_all[k:k + 128]
            src = Path(tmp) / "t.html"
            src.write_text("<!doctype html>" + CSS + "".join(table(x, y, n, c) for x, y, c in batch))
            out = subprocess.run(["xvfb-run", "-a", exe, str(helper), str(src), str(PITCH)],
                                 capture_output=True, text=True, timeout=300)
            if out.returncode:
                raise RuntimeError(out.stderr.strip()[-300:])
            import json
            data = json.loads(out.stdout.strip().splitlines()[-1])
            version = data["version"]
            m, w = check("webkitgtk", n, data["tables"], batch)
            mism += m; wrong += w
    return f"WebKitGTK {version}", len(batch_all), mism, wrong


ENGINES = {"chromium": chromium, "firefox": desktop("Firefox"), "safari": desktop("Safari"), "webkitgtk": webkitgtk,
           "weasyprint": weasyprint_engine, "qtwebkit": qtwebkit}

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    sample = int(sys.argv[2]) if len(sys.argv) > 2 else None
    ok = True
    for name, fn in ENGINES.items():
        try:
            eng, count, mism, wrong = fn(n, sample)
        except Exception as e:                                   # engine not installed here
            print(f"{name}: skipped ({type(e).__name__}: {e})"); continue
        print(f"{eng}: {count} tables of {n} bits; layouts differing from the spec: {mism}; wrong sums: {wrong}")
        ok &= mism == 0 and wrong == 0
    sys.exit(0 if ok else 1)

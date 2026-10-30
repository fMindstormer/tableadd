"""Measure where WebKitGTK puts every table cell: python3 tests/webkitgtk_layout.py page.html PITCH

Prints JSON: for each table in the page, for each row, the column of each cell (its left edge minus the
table's, divided by PITCH). Needs the system Python with PyGObject and WebKitGTK (Ubuntu:
gir1.2-webkit2-4.1), and a display: run it under xvfb-run. tests/engines.py does all of that."""
import json
import os
import sys

os.environ.setdefault("WEBKIT_DISABLE_DMABUF_RENDERER", "1")
os.environ.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")

import gi  # noqa: E402

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import GLib, Gtk, WebKit2  # noqa: E402

MEASURE = """JSON.stringify([...document.getElementsByTagName('table')].map(t => {
  const L = t.getBoundingClientRect().left;
  return [...t.rows].map(r => [...r.cells].map(c => Math.round((c.getBoundingClientRect().left - L) / %s)));
}))"""


def main(path, pitch):
    html = open(path, encoding="utf-8").read()
    window = Gtk.OffscreenWindow()
    window.set_default_size(1600, 900)
    view = WebKit2.WebView()
    window.add(view)
    window.show_all()
    result = {}

    def measured(view, task):
        try:
            result["json"] = view.evaluate_javascript_finish(task).to_string()
        except GLib.Error as e:
            result["error"] = str(e)
        Gtk.main_quit()

    def changed(view, event):
        if event == WebKit2.LoadEvent.FINISHED:
            view.evaluate_javascript(MEASURE % pitch, -1, None, None, None, measured)

    view.connect("load-changed", changed)
    GLib.timeout_add_seconds(120, Gtk.main_quit)
    view.load_html(html, "file:///")
    Gtk.main()
    if "json" not in result:
        sys.exit(f"WebKitGTK gave no layout: {result.get('error', 'timed out')}")
    v = WebKit2.get_major_version(), WebKit2.get_minor_version(), WebKit2.get_micro_version()
    print(json.dumps({"version": ".".join(map(str, v)), "tables": json.loads(result["json"])}))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 10)

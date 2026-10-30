"""Real engines must place every cell where the specification does (and so compute the right sums)."""
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engines  # noqa: E402


def test_chromium_every_4bit_sum():
    pytest.importorskip("playwright")
    _, count, mism, wrong = engines.chromium(4)
    assert (count, mism, wrong) == (512, 0, 0)


def test_chromium_random_8bit_sums():
    pytest.importorskip("playwright")
    _, count, mism, wrong = engines.chromium(8, sample=128)
    assert (mism, wrong) == (0, 0)


def test_webkitgtk_every_4bit_sum():
    if not (engines.gi_python() and shutil.which("xvfb-run")):
        pytest.skip("needs WebKitGTK with PyGObject (Ubuntu: gir1.2-webkit2-4.1) and xvfb-run")
    _, count, mism, wrong = engines.webkitgtk(4)
    assert (count, mism, wrong) == (512, 0, 0)


def test_weasyprint_every_4bit_sum():
    pytest.importorskip("weasyprint")
    _, count, mism, wrong = engines.weasyprint_engine(4)
    assert (count, mism, wrong) == (512, 0, 0)


def test_qtwebkit_every_4bit_sum():
    if not (shutil.which("wkhtmltopdf") and shutil.which("pdftotext")):
        pytest.skip("needs wkhtmltopdf and pdftotext")
    _, count, mism, wrong = engines.qtwebkit(4)
    assert (count, mism, wrong) == (512, 0, 0)

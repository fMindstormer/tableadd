"""The adder, laid out with the specification's algorithm (tableadd.table)."""
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tableadd import PROGRAM, add, columns, rows, subtract  # noqa: E402
from tableadd.adder import bits  # noqa: E402
from tableadd.html import table  # noqa: E402
from tableadd.table import place_row  # noqa: E402


def test_every_4bit_sum():
    assert all(add(x, y, 4, c) == x + y + c for x in range(16) for y in range(16) for c in (0, 1))


def test_random_16bit_sums():
    rng = random.Random(0)
    for _ in range(300):
        x, y, c = rng.randrange(2 ** 16), rng.randrange(2 ** 16), rng.randrange(2)
        assert add(x, y, 16, c) == x + y + c


def test_every_4bit_difference():
    assert all(subtract(x, y, 4) == ((x - y) % 16, x >= y) for x in range(16) for y in range(16))


def test_random_16bit_differences():
    rng = random.Random(1)
    for _ in range(300):
        x, y = rng.randrange(2 ** 16), rng.randrange(2 ** 16)
        assert subtract(x, y, 16) == ((x - y) % 2 ** 16, x >= y)


def test_a_subtraction_table_is_an_addition_table():
    """Swapping b's pairs gives, byte for byte, the table for x + NOT y + 1, so every engine check of all 4-bit
    sums with carry in has already laid out every 4-bit subtraction."""
    for x in range(16):
        for y in range(16):
            assert table(x, y, 4, 1, invert_b=True) == table(x, 15 - y, 4, 1)


def test_program_rows_are_the_same_html():
    html = table(173, 85, 8)
    trs = html.split("<tr>")[2:]
    assert len(trs) == 8 and len(set(t.replace("</table>", "") for t in trs)) == 1


def rowspans(html):
    return [[int(v) for v in re.findall(r'rowspan="(\d+)"', tr)] for tr in html.split("<tr>")[1:]]


def test_readme_style_has_the_same_rowspans():
    for x, y, n, c in [(3, 3, 2, 0), (11, 6, 4, 1), (173, 85, 8, 0)]:
        marked = table(x, y, n, c, style="readme")
        assert rowspans(marked) == rowspans(table(x, y, n, c))
        assert len(set(marked.split("\n")[2:2 + n])) == 1          # the repeated rows are identical lines


def test_the_readme_table_is_3_plus_3():
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
    live = readme[readme.index("<table>"):readme.index("</table>") + len("</table>")]
    assert live == table(3, 3, 2, style="readme")
    assert add(3, 3, 2) == 6


def test_every_program_row_uses_exactly_its_cells():
    """No cell spills past the right edge: each program row has exactly len(PROGRAM) free columns."""
    for x, y, c in [(0, 0, 0), (255, 255, 1), (170, 86, 0), (13, 200, 1)]:
        a, b = bits(x, 8), bits(y, 8)
        width = len(columns(a, b, c))
        cov = []
        for r, row in enumerate(rows(a, b, c)):
            if r > 0:
                assert sum(1 for v in cov if v == 0) == len(PROGRAM) and len(cov) == width
            _, cov = place_row(cov, row)

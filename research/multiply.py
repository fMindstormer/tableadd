"""A 2-bit multiplier whose rows after the first are all the same line of HTML: python research/multiply.py

This gadget is special to two bits, whose columns hold at most two partial products; research/product_scan.py
multiplies any width, with a bigger table.

For a = a1a0 and b = b1b0 the product, column by column, is
    p0 = a0b0,   p1 = a1b0 xor a0b1 with carry c1 = a1b0 and a0b1,   p2 = c1 xor a1b1,   p3 = c1 and a1b1.
So every step is one gadget, G(n; x, y) = (n xor xy, n and xy). It wakes in its row inside the pairs for x and
y, each written twice in the first row, and to the right of its state n, so its readers find v = n + 2x + 2y
free columns to their left. xy shows in v because 2x + 2y is 4 only when both are 1. Reader j gets the
repeated row's cell PROGRAM[v + j], which has rowspan 1 only at positions 5, 7 and 8:

    reader 0   free again in the next row when v = 5:         n and xy   (the state for the next gadget)
    reader 4   free again when v is 1, 3 or 4:                n xor xy   (a bit of the product)

The next gadget sits between reader 0 and reader 1, so of this row's readers it counts only reader 0, and the
state needs no wire, as with the adder's carry. The first two gadgets have no state yet: one column that wakes
with them stands in for n = 1, so that n and xy is just xy.

Readers 5 to 8, the program's cells from position 10 on, and the spare columns only keep the table tidy, as
in the adder: every column consumed on the right lands on rowspan 999 and is covered for good, and every
repeated row has exactly 17 free columns. With readers 0 to 4 and the first ten cells, the same length as the
adder's program, all 16 products still come out right, but some consumed columns stay free off to the right
of everything still to happen.

    g0 (row 1)  G(1; a0, b0)    reader 0 is p0
    g1 (row 2)  G(1; a1, b0)    reader 0 is a1b0, the state of g2
    g2 (row 3)  G(a1b0; a0, b1) reader 4 is p1, reader 0 is c1, the state of g3
    g3 (row 4)  G(c1; a1, b1)   reader 4 is p2, reader 0 is p3

g1, g2 and g3 nest like the adder's full adders. g0 sits to the right of all of them, so in row 2 what is left
of it counts towards nothing. Spare columns fill the rows that would otherwise have fewer than 17 free
columns, so no cell spills past the right edge.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tableadd.adder import bits  # noqa: E402
from tableadd.table import lay_out, place_row  # noqa: E402

H = 999
PROGRAM = [1 if j in (5, 7, 8) else H for j in range(17)]
READERS = 9


def gadget(g, w, x, y, state, inner=()):
    """The columns of gadget g, which reads in row w. state 'one': a column that wakes with it stands in for
    n = 1; state 'given': n is whatever the gadget around it leaves free on the left."""
    pair = lambda name, bit: ([(f"{g}.{name}{c}", w if bit else H) for c in (0, 1)],
                              [(f"{g}.{name}{c}.not", H if bit else w) for c in (1, 0)])
    (xl, xr), (yl, yr) = pair("x", x), pair("y", y)
    one = [(f"{g}.one", w)] if state == "one" else []
    return (one + xl + yl + [(f"{g}.r0", w)] + list(inner) +
            [(f"{g}.r{j}", w) for j in range(1, READERS)] + yr + xr)


def columns(a, b):
    """The first row: (name, rowspan) per column. a, b: two bits each, least significant first."""
    (a0, a1), (b0, b1) = a, b
    g3 = gadget("g3", 4, a1, b1, "given")
    g2 = gadget("g2", 3, a0, b1, "given", g3)
    g1 = gadget("g1", 2, a1, b0, "one", g2)
    g0 = gadget("g0", 1, a0, b0, "one")
    spare = [("spare1.0", 1), ("spare1.1", 1), ("spare1.2", 1), ("spare3", 3), ("spare4", 4)]
    return g1 + g0 + spare


def rows(a, b):
    return [[h for _, h in columns(a, b)]] + [list(PROGRAM) for _ in range(4)]


OUTPUTS = [(1, "g0.r0"), (3, "g2.r4"), (4, "g3.r4"), (4, "g3.r0")]   # (row, column) of p0, p1, p2, p3


def decode(a, b, layout):
    """Bit i of the product is 1 when the cell that landed on OUTPUTS[i] has rowspan 1."""
    col = {name: x for x, (name, _) in enumerate(columns(a, b))}

    def rowspan_at(r, name):
        return next((h for x, h in zip(layout[r], PROGRAM) if x == col[name]), None)

    return sum((rowspan_at(r, name) == 1) << i for i, (r, name) in enumerate(OUTPUTS))


def multiply(x, y):
    a, b = bits(x, 2), bits(y, 2)
    return decode(a, b, lay_out(rows(a, b)))


def html(x, y):
    """The table for x * y, rowspans only. The rows after the first are the same string."""
    first = "".join(f'<td rowspan="{h}"></td>' for _, h in columns(bits(x, 2), bits(y, 2)))
    prog = "".join(f'<td rowspan="{h}"></td>' for h in PROGRAM)
    return f"<table><tr>{first}</tr>" + f"<tr>{prog}</tr>" * 4 + "</table>"


if __name__ == "__main__":
    wrong = [(x, y, multiply(x, y)) for x in range(4) for y in range(4) if multiply(x, y) != x * y]
    free = set()
    for x in range(4):
        for y in range(4):
            cov = []
            for r, row in enumerate(rows(bits(x, 2), bits(y, 2))):
                if r:
                    free.add(sum(1 for v in cov if v == 0))
                _, cov = place_row(cov, row)
    width = len(columns(bits(0, 2), bits(0, 2)))
    print(f"16 products, laid out with the specification's algorithm: {16 - len(wrong)} right, wrong: {wrong}")
    print(f"{width} columns, 4 repeated rows of {len(PROGRAM)} cells; free columns per repeated row: {sorted(free)}")

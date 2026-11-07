"""A ripple-carry adder whose program rows are identical.

Bits are dual-rail: bit x is a pair of columns (P, N), and in the row where it is read exactly one of them
is free (P if x = 1, N if x = 0). Outside the pair it therefore always counts as exactly one free slot, and
only columns physically between P and N count the bit itself.

Every row after the first is the same PROGRAM: ten cells whose rowspans are 1 at positions 3 and 5 and H
('until the end of the table') elsewhere. A column that is free in a row receives the program cell whose
position equals the number of free columns to its left; that number is all the column learns.

Full adder i wakes in row i+1 and occupies, from left to right,
    Pa Pb R1 R2 [full adder i+1] R3 R4 R5 R6 Nb Na
Its six readers count s = a + b + carry (plus a constant), so reader Rj gets rowspan 1 exactly when
PROGRAM[s + j - 1] == 1:
    R1: s = 3     R2: s = 2      -> one of them is free in row i+2 exactly when there is a carry
    R3: s odd     R4: s even     -> the sum bit, dual-rail
    R5: s = 1     R6: s = 0      -> together 'no carry', which keeps the block neutral to its right
Full adder i+1 sits between R2 and R3, so in its row it counts R1 + R2: the carry, with no wire.

Swapping the two columns of a pair inverts its bit. With b's pairs swapped and the carry in tied to 1 the same
table computes a + NOT b + 1 = a - b + 2^n: the sum bits are a - b mod 2^n, and the carry out says a >= b.
"""
from .table import lay_out

H = 999                                   # covers a column to the end of the table (browsers clamp it)
PROGRAM = [H, H, H, 1, H, 1, H, H, H, H]  # the repeated row: 10 cells, rowspan 1 at positions 3 and 5


def columns(a, b, carry_in=0, invert_b=False):
    """The first row: (name, rowspan) for each column, left to right. rowspan = the row in which that column
    first becomes free (H = never). a, b: lists of bits, least significant first. invert_b swaps b's pairs, so
    the adders read NOT b."""
    n = len(a)

    def full_adder(i):
        w = i + 1                                     # full adder i reads in row i + 1
        pb, nb = (f"b{i}", w if b[i] else H), (f"b{i}.not", w if not b[i] else H)
        if invert_b:
            pb, nb = nb, pb
        cols = [(f"a{i}", w if a[i] else H), pb, (f"carry{i}.3", w), (f"carry{i}.2", w)]
        if i + 1 < n:
            cols += full_adder(i + 1)
        cols += [(f"sum{i}", w), (f"sum{i}.not", w), (f"nocarry{i}.1", w), (f"nocarry{i}.0", w),
                 nb, (f"a{i}.not", w if not a[i] else H)]
        return cols

    # the carry-in is dual-rail too, and one spare column fills row 1, so that every program row has exactly
    # as many free columns as the program has cells: nothing spills past the right edge
    return ([("cin", 1 if carry_in else H)] + full_adder(0) +
            [("cin.not", 1 if not carry_in else H), ("spare", 1)])


def rows(a, b, carry_in=0, invert_b=False):
    """All rows of the table: the first row, then len(a) identical program rows."""
    return [[h for _, h in columns(a, b, carry_in, invert_b)]] + [list(PROGRAM) for _ in range(len(a))]


def decode(a, b, carry_in, layout):
    """Read the sum from a layout (columns of each cell, per row, as the browser or lay_out placed them):
    sum bit i is 1 when the cell that landed on column sum<i> in row i+1 has rowspan 1."""
    n = len(a)
    names = [c for c, _ in columns(a, b, carry_in)]
    col = {name: x for x, name in enumerate(names)}

    def rowspan_at(r, name):
        return next((h for x, h in zip(layout[r], PROGRAM) if x == col[name]), None)

    total = sum((rowspan_at(i + 1, f"sum{i}") == 1) << i for i in range(n))
    carry = rowspan_at(n, f"carry{n - 1}.3") == 1 or rowspan_at(n, f"carry{n - 1}.2") == 1
    return total + (carry << n)


def bits(v, n):
    return [(v >> i) & 1 for i in range(n)]


def add(x, y, n, carry_in=0):
    """x + y (+ carry_in), computed by laying out the table with the specification's algorithm."""
    a, b = bits(x, n), bits(y, n)
    return decode(a, b, carry_in, lay_out(rows(a, b, carry_in)))


def subtract(x, y, n):
    """(x - y mod 2^n, x >= y), computed by laying out the adder with y's pairs swapped and carry in 1."""
    a, b = bits(x, n), bits(y, n)
    total = decode(a, b, 1, lay_out(rows(a, b, 1, invert_b=True)))
    return total % 2 ** n, total >= 2 ** n

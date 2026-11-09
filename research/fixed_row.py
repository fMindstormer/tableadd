"""Parity and inner product mod 2 with one fixed repeated row: python research/fixed_row.py [N | --search]

N (default 4): check every input up to 2N bits of parity and N pairs of inner product.

Every repeated row is the same three cells, whatever the number of input bits:

    <td rowspan="999"></td><td rowspan="2"></td><td rowspan="3"></td>

As research/positions.py shows, the reader at the right of the first row learns only F_s, the number of free
columns to its left in row s, and F_{s+1} is worked out from F_s, F_{s-1}, F_{s-2} and the number e of columns
to its left that wake in row s + 1. With this row,

    F_{s+1} = max(F_s - 3, 0) + [F_{s-1} >= 2] + [F_{s-2} >= 3] + e:

of the free columns, the first gets rowspan 999 and is gone, the second sleeps one row, the third two rows, and
the rest get no cell and stay free. Write the state as (F_s, F_{s-1}, F_{s-2}). With e = 1 in every row it
swings between U = (1, 2, 1) and V = (2, 1, 2), and that swing holds a bit.

A stretch of rows whose inputs depend on a few input bits acts on the pair {U, V}:

    FLIP  five rows, e = 2 3 0 0 0 if x = 0 and 1 1 1 1 1 if x = 1; it keeps U and V if x = 0 and swaps them
          if x = 1.
    AND   nine rows, linear in x and y; it swaps U and V only if x = y = 1:
              x y = 0 0:  1 1 2 2 0 0 1 1 1        0 1:  1 1 1 2 2 2 0 0 0
                    1 0:  2 2 1 0 0 1 1 1 1        1 1:  2 2 0 0 2 3 0 0 0
          (each row's e is the 0 0 value, plus x times the 1 0 change, plus y times the 0 1 change).

Each e is written into the first row: a cell with rowspan s always wakes in row s; a cell with rowspan s if x = 1
and 999 if x = 0 adds x; the other way round adds NOT x. Three rows with e = 1, 2, 1 bring the chain to U.
The stretches follow one another, one per input bit or pair of bits. In the last row the reader's own column
is free at last, and the cell it gets has rowspan 2 if the chain is at U and rowspan 3 if it is at V.

    parity of n bits                  n FLIP stretches    5n + 3 repeated rows
    inner product mod 2 of n pairs    n AND stretches     9n + 3 repeated rows

U and V are unordered: neither has at least as many free columns as the other in all three rows. That is
what a swap needs. The update never gives fewer free columns for more, so two runs of the chain fed the same
input that are ordered stay ordered, and an ordered pair can never be swapped. For the same reason no stretch
does this with a row whose cells have rowspans 1, 2 and 999 only: there the state is the last two counts, and
two runs that are unordered stay so only if the one ahead changes every row, so a stretch's length alone
decides whether it keeps or swaps the pair, and both of its inputs do the same.

python research/fixed_row.py --search reruns the searches behind FLIP and AND (it needs numpy). With up to 3
columns waking per row, it tries every row of up to 3 cells with rowspans 1, 2, 3 and 999 for stretches of 1
to 5 rows that keep an unordered pair for x = 0 and swap it for x = 1: only 999 2 3 and 999 3 2 have one, and
only with 5 rows (--search 4 4: none of 4 rows or fewer with rows of up to 4 cells either). For 999 2 3 it then
lists every stretch of up to 12 rows that maps {U, V} onto itself. Whether one swaps is an affine function of
its inputs mod 2 up to 6 rows, so no stretch of 6 rows or fewer swaps on x AND y alone; 7 and 8 rows have none
either, and 9 rows have AND. No stretch of up to 12 rows with inputs linear in three bits swaps on a function
with a term in all three, such as x AND y AND z.

The columns after the reader keep every repeated row at least three free columns wide, so no cell spills; the
answer does not depend on them.
"""
import sys
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tableadd.table import lay_out, place_row  # noqa: E402

H = 999
PROGRAM = [H, 2, 3]
U, V = (1, 2, 1), (2, 1, 2)
START = (1, 2, 1)
FLIP = {(0,): (2, 3, 0, 0, 0), (1,): (1, 1, 1, 1, 1)}
AND = {(0, 0): (1, 1, 2, 2, 0, 0, 1, 1, 1), (0, 1): (1, 1, 1, 2, 2, 2, 0, 0, 0),
       (1, 0): (2, 2, 1, 0, 0, 1, 1, 1, 1), (1, 1): (2, 2, 0, 0, 2, 3, 0, 0, 0)}


def step(state, e):
    """The chain's state one row on, from the recurrence."""
    f, f1, f2 = state
    return (max(f - 3, 0) + (f1 >= 2) + (f2 >= 3) + e, f, f1)


def run(state, word):
    for e in word:
        state = step(state, e)
    return state


def check_stretches():
    """FLIP and AND act on {U, V} as claimed, and their inputs are affine in their bits."""
    for words, flips in ((FLIP, lambda a: a[0]), (AND, lambda a: a[0] & a[1])):
        for bits, word in words.items():
            assert (run(U, word), run(V, word)) == ((V, U) if flips(bits) else (U, V)), (bits, word)
        _rows(words)
    s = (0, 0, 0)
    for e in START:
        s = step(s, e)
    assert s == U


def _rows(words):
    """Per row: (constant, coefficient of each bit), checked to reproduce every word."""
    m = len(next(iter(words)))
    base = words[(0,) * m]
    unit = [words[tuple(int(i == j) for j in range(m))] for i in range(m)]
    rows = [(base[t], [u[t] - base[t] for u in unit]) for t in range(len(base))]
    for bits, word in words.items():
        assert all(c + sum(a * b for a, b in zip(cs, bits)) == word[t] for t, (c, cs) in enumerate(rows))
    return rows


class Table:
    """A first row with the stretches in order, then the reader, then spare columns."""

    def __init__(self, stretches):
        self.stretches = stretches      # [(names of the stretch's bits, words)]
        self.R = len(START) + sum(len(next(iter(w.values()))) for _, w in stretches)
        self.spares = []
        self._fill_spares()

    def columns(self, value):
        """(name, rowspan) for the first row; value maps each bit's name to 0 or 1."""
        cols, row = [], 1
        for e in START:
            cols += [(f"start.r{row}.{c}", row) for c in range(e)]
            row += 1
        for names, words in self.stretches:
            for const, coef in _rows(words):
                k = const - sum(-a for a in coef if a < 0)
                assert k >= 0
                cols += [(f"r{row}.{c}", row) for c in range(k)]
                for nm, a in zip(names, coef):
                    on, off = (row, H) if a > 0 else (H, row)
                    cols += [(f"r{row}.{nm}{'' if a > 0 else '.not'}.{c}", on if value[nm] else off)
                             for c in range(abs(a))]
                row += 1
        return cols + [("reader", self.R)] + self.spares

    def bits(self):
        return [nm for names, _ in self.stretches for nm in names]

    def rows(self, value):
        return [[h for _, h in self.columns(value)]] + [list(PROGRAM)] * self.R

    def read(self, value):
        """The reader's cell in row R: 0 if it has rowspan 2, 1 if rowspan 3."""
        cols = self.columns(value)
        reader = next(i for i, (nm, _) in enumerate(cols) if nm == "reader")
        layout = lay_out(self.rows(value))
        got = [PROGRAM[j] for j, c in enumerate(layout[self.R]) if c == reader]
        return {(2,): 0, (3,): 1}.get(tuple(got))

    def width(self):
        return len(self.columns({nm: 0 for nm in self.bits()}))

    def inputs(self):
        names = self.bits()
        return [dict(zip(names, vs)) for vs in product((0, 1), repeat=len(names))]

    def _fill_spares(self):
        while True:
            short = None
            for value in self.inputs():
                cov = []
                for r, row in enumerate(self.rows(value)):
                    if r and sum(1 for c in cov if c == 0) < len(PROGRAM):
                        short = r if short is None else min(short, r)
                        break
                    _, cov = place_row(cov, row)
            if short is None:
                return
            self.spares.append((f"spare{len(self.spares)}", short))


def parity_table(n):
    return Table([((f"x{i}",), FLIP) for i in range(n)])


def inner_product_table(n):
    return Table([((f"x{i}", f"y{i}"), AND) for i in range(n)])


# --- the searches ------------------------------------------------------------------------------------------

EMAX = 3                                 # columns waking per row, at most


def flip_rows(L, kmax):
    """Every row of up to kmax cells (rowspans 1, 2, 3, 999) with a stretch of L rows that keeps an unordered
    pair of states for x = 0 and swaps it for x = 1, states up to the row's length + 3."""
    import numpy as np
    found = []
    for k in range(2, kmax + 1):
        for program in product([1, 2, 3, H], repeat=k):
            hs = sorted({q for q in program if q not in (1, H)})
            if not hs:
                continue
            depth, box = max(hs), k + 3
            vals = np.arange(box + L * EMAX + 2)
            A = np.array([sum(1 for r in range(f) if r >= k or program[r] == 1) for f in vals])
            B = {h: np.array([sum(1 for r in range(min(f, k)) if program[r] == h) for f in vals]) for h in hs}
            states = np.array(list(product(range(box + 1), repeat=depth)))
            code = (box + 1) ** np.arange(depth)[::-1]          # a state's code is its index in states
            idx = np.arange(len(states))
            fixed, swaps = np.zeros(len(states), dtype=object), set()   # fixed: bitmask of the words fixing it
            for wi, word in enumerate(product(range(EMAX + 1), repeat=L)):
                t = states
                for e in word:
                    t = np.column_stack([A[t[:, 0]] + sum(B[h][t[:, h - 1]] for h in hs) + e, t[:, :-1]])
                img = np.where((t <= box).all(axis=1), t @ code, -1)
                for i in np.nonzero(img == idx)[0]:
                    fixed[i] |= 1 << wi
                for i in np.nonzero((img >= 0) & (img != idx))[0]:
                    if img[img[i]] == i:
                        swaps.add((i, img[i]))
            if any(fixed[i] & fixed[j] for i, j in swaps):
                found.append(program)
    return found


def returning(L):
    """Every stretch of L rows that maps {U, V} onto itself, for the row 999 2 3: word -> does it swap."""
    out = {}

    def go(p, q, word, total):
        if len(word) == L:
            if {p, q} == {U, V}:
                out[word] = p == V
            return
        for e in range(EMAX + 1):
            if total + e > L:     # U and V hold two live columns each and a row loses at most one, so a
                                      # stretch that comes back has inputs totalling at most L
                break
            go(step(p, e), step(q, e), word + (e,), total + e)
    go(U, V, (), 0)
    return out


def affine(words):
    """Is 'swaps' c . (word mod 2) + d over GF(2) for some c, d? Gaussian elimination."""
    rows = [[e % 2 for e in w] + [1, int(f)] for w, f in words.items()]
    r = 0
    for col in range(len(rows[0]) - 1):
        i = next((i for i in range(r, len(rows)) if rows[i][col]), None)
        if i is None:
            continue
        rows[r], rows[i] = rows[i], rows[r]
        rows = [[a ^ b for a, b in zip(row, rows[r])] if j != r and row[col] else row for j, row in enumerate(rows)]
        r += 1
    return all(any(row[:-1]) or not row[-1] for row in rows)


def squares(words):
    """Four stretches a, b, c, b + c - a, the inputs for x y = 00, 01, 10, 11 when every row's input is linear in
    x and y: (a, c - a, b - a) -> how many of the four swap, mod 2."""
    out = {}
    for a in words:
        for b in words:
            for c in words:
                d = tuple(y + z - x for x, y, z in zip(a, b, c))
                if d in words:
                    out[a, tuple(z - x for x, z in zip(a, c)), tuple(y - x for x, y in zip(a, b))] = \
                        (words[a] + words[b] + words[c] + words[d]) % 2
    return out


def search(L, kmax, Lmax=12):
    for length in range(1, L + 1):
        print(f"rows of up to {kmax} cells with a {length}-row stretch that keeps an unordered pair for x = 0 "
              f"and swaps it for x = 1: {flip_rows(length, kmax) or 'none'}", flush=True)
    for length in range(1, Lmax + 1):
        words = returning(length)
        sq = squares(words)
        and_ = sum(sq.values())
        cube = False
        by_dir = {}
        for (a, al, be), odd in sq.items():
            if any(al) and any(be):
                by_dir.setdefault((al, be), {})[a] = odd
        for bases in by_dir.values():
            cube = cube or len(set(bases.values())) > 1     # two parallel squares, one odd: an odd cube
        print(f"999 2 3, {length} rows: {len(words)} stretches map {{U, V}} onto itself, "
              f"{sum(words.values())} swap; affine mod 2: {affine(words)}; "
              f"with an x y term: {and_}; with an x y z term: {'some' if cube else 'none'}", flush=True)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--search"]:           # --search L K: only the rows search, up to L rows and K cells
        search(*map(int, sys.argv[2:4]), Lmax=0) if len(sys.argv) > 3 else search(5, 3)
        sys.exit()
    check_stretches()
    top = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    for n in range(1, 2 * top + 1):
        t = parity_table(n)
        wrong = sum(t.read(v) != sum(v.values()) % 2 for v in t.inputs())
        print(f"parity of {n} bits: {2 ** n} inputs, {wrong} wrong; {t.width()} columns "
              f"({len(t.spares)} spare), {t.R} repeated rows", flush=True)
    for n in range(1, top + 1):
        t = inner_product_table(n)
        wrong = sum(t.read(v) != sum(v[f"x{i}"] & v[f"y{i}"] for i in range(n)) % 2 for v in t.inputs())
        print(f"inner product mod 2 of {n} pairs: {4 ** n} inputs, {wrong} wrong; {t.width()} columns "
              f"({len(t.spares)} spare), {t.R} repeated rows", flush=True)

"""n-bit multiplication by tables whose rows after the first are identical: python research/product_scan.py [N ...]

The product is worked out column by column (product scanning), one partial product per repeated row, plus a
row for the top bit: n*n + 1 rows for n >= 2 bits. A count T, the carry plus the partial products of the
current column added so far, is passed from gadget to gadget.
As with the adder, gadget t + 1 sits between gadget t's left and right readers, so it counts how many of
the columns left of it are free again, and that number is the state. Every rank up to gadget t's last left
reader holds such a column, so the state is P(v + o), the count of the program's 1s up to a position that
moves with v. Every state update is therefore a window of one staircase, and the program is that staircase:
a block of 999s, then two segments, one per kind of gadget.

    first gives a0b0, the product's bit 0: it reads x + y, with no left readers, so it passes on 0, and its
          bit is the first reader whose rank reads 999 999 1, at the end of the block of 999s.
    acc   adds the partial product xy to a count T <= m. A gadget cannot do that by itself (T + xy is not a
          non-decreasing function of any weighted sum of T, x and y), so it is split in two. The gadget reads
          u = T + (m+1)(x + y) and passes on u - [u >= m+1] = (T + xy) + m(x + y), and the next gadget takes
          away m(x + y) by reading NOT x and NOT y, written m times each, along with its own inputs. The acc
          segment is a run of 1s with one hole; a gadget with a smaller bound starts its window further along
          the first run, so one segment serves every m.
    last  adds a column's last partial product and halves, for an odd bound m. It reads u = T + (m+1)(x + y)
          and passes on floor((T + xy) / 2) + (m+1)/2 (x + y), the carry into the next column plus a part the
          next gadget takes away; the halving segment alternates 0 and 1 with one slip, two 1s in a row. A
          smaller odd bound starts its window an even number of places further along. The reader right after
          the window lands on (T + xy) mod 2: that is the column's bit of the product, as with the adder's R3.
    top   reads the last carry, the product's top bit, with the first reader whose rank reads 999 1.

The bound of each step is what all-ones inputs reach, so the input columns are written as few times as
each step allows. The block of 999s only has to be long enough that every window can be reached from its
gadget's first reader. Consumed columns are not all covered for good here, unlike in the adder: those that
land on a 1 stay free where they are, to the right of everything still to happen or, on the left, counted
into the state. Spare
columns at the right end keep every row at least as wide as the program, so no cell spills.
"""
import sys
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tableadd.table import lay_out, place_row  # noqa: E402

H = 999


def schedule(n):
    """One gadget per partial product, column by column, and one more: ('first', 'a0', 'b0', 0) gives a0b0 and
    passes nothing on; ('acc', x, y, m) adds xy to a count of at most m; ('last', x, y, m) adds a column's last
    partial product and halves, m odd and at least the count; ('top', None, None, 0) reads the last carry, the
    product's top bit."""
    steps, carry = [], 0
    for c in range(2 * n - 1):
        pps = [(f"a{i}", f"b{c - i}") for i in range(n) if 0 <= c - i < n]
        for k, (x, y) in enumerate(pps):
            if c == 0:
                steps.append(("first", x, y, 0))
            else:
                steps.append(("acc", x, y, carry + k) if k + 1 < len(pps) else ("last", x, y, (carry + k) | 1))
        carry = (carry + len(pps)) // 2
    return steps + [("top", None, None, 0)] if n > 1 else steps


class Construction:
    def __init__(self, n, halving_first=None):
        if halving_first is None:        # whichever order of the two segments gives the narrower table
            a, b = Construction(n, False), Construction(n, True)
            self.__dict__ = (a if a.width() <= b.width() else b).__dict__
            return
        self.n, self.steps = n, schedule(n)
        kinds = [kind for kind, *_ in self.steps]
        M = max((m for kind, *_, m in self.steps if kind == "acc"), default=0)
        Mh = max((m for kind, *_, m in self.steps if kind == "last"), default=1)
        acc = [0 if u == M + 1 else 1 for u in range(1, 3 * M + 3)] if "acc" in kinds else []
        halve = ([1 - x % 2 if x <= 2 * Mh + 2 else 1 if x == 2 * Mh + 3 else x % 2 for x in range(1, 3 * Mh + 4)]
                 if "last" in kinds else [])
        segs = [("last", halve), ("acc", acc)] if halving_first else [("acc", acc), ("last", halve)]
        rel, base, at, ones = {}, {}, 0, 0          # where each segment starts, and the 1s before it
        for name, seg in segs:
            rel[name], base[name] = at, ones
            at, ones = at + len(seg), ones + sum(seg)
        # for each gadget: how many columns are free left of its first reader, apart from u
        self.carry, prev = [], None
        for step in self.steps:
            self.carry.append(0 if prev is None or prev[0] == "first" else
                              base["acc"] + M + prev[3] if prev[0] == "acc" else base["last"] + Mh + 1)
            prev = step
        # where the windows of acc and last gadgets start, relative to the end of the block of 999s
        target = {t: rel["acc"] + M - m if kind == "acc" else rel["last"] + 2 * (Mh - m)
                  for t, (kind, *_, m) in enumerate(self.steps) if kind in ("acc", "last")}
        z = max([self.carry[t] - target[t] for t in target] + [2 if "first" in kinds else 0])
        self.program = [H] * z + [1 if q else H for _, s in segs for q in s]
        # readers: left of the gadget nested inside, right of it, and which of them are bits of the product
        self.left, self.right, self.observed, self.weight = [], [], [], []
        for t, (kind, x, y, m) in enumerate(self.steps):
            if kind in ("acc", "last"):
                self.left.append(z + target[t] - self.carry[t])
                self.right.append(1 if kind == "last" else 0)
                self.observed.append([self.left[t]] if kind == "last" else [])
                self.weight.append(m + 1)
            elif kind == "first":       # u = x + y; the bit is the first reader whose rank reads 999 999 1
                j = self._find(0, [H, H, 1])
                self.left.append(0), self.right.append(j + 1), self.observed.append([j]), self.weight.append(1)
            else:                       # top: u is the last carry, the first reader whose rank reads 999 1
                j = self._find(self.carry[t], [H, 1])
                self.left.append(j + 1), self.right.append(0), self.observed.append([j]), self.weight.append(0)
        self.spares = []
        self._fill_spares()

    def _find(self, start, cells):
        """The first j from which the program reads cells at rank start + j, extending the program if need be."""
        j = next(j for j in range(len(self.program) + 1)
                 if all(start + j + i >= len(self.program) or self.program[start + j + i] == c for i, c in enumerate(cells)))
        self.program += cells[len(self.program) - start - j:]
        return j

    def gadget(self, t, bitval):
        """Columns of gadget t (reading in row t + 1), with the rest of the chain between its readers."""
        w = t + 1
        kind, x, y, m = self.steps[t]
        reads = []                                   # (input bit, value as read, copies)
        if t and self.steps[t - 1][0] != "first":
            pkind, px, py, pm = self.steps[t - 1]
            k = pm if pkind == "acc" else (pm + 1) // 2
            reads += [(f"not.{px}", 1 - bitval[px], k), (f"not.{py}", 1 - bitval[py], k)]
        if kind != "top":
            reads += [(x, bitval[x], self.weight[t]), (y, bitval[y], self.weight[t])]
        left = [(f"g{t}.{nm}.{c}", w if b else H) for nm, b, k in reads for c in range(k)]
        right = [(f"g{t}.{nm}.{c}.not", H if b else w) for nm, b, k in reversed(reads) for c in range(k)]
        nl, nr = self.left[t], self.right[t]
        inner = self.gadget(t + 1, bitval) if t + 1 < len(self.steps) else []
        return (left + [(f"g{t}.r{j}", w) for j in range(nl)] + inner +
                [(f"g{t}.r{j}", w) for j in range(nl, nl + nr)] + right)

    def columns(self, xv, yv):
        bitval = {f"a{i}": (xv >> i) & 1 for i in range(self.n)} | {f"b{i}": (yv >> i) & 1 for i in range(self.n)}
        return self.gadget(0, bitval) + self.spares

    def width(self):
        return len(self.columns(0, 0))

    def rows(self, xv, yv):
        return [[h for _, h in self.columns(xv, yv)]] + [list(self.program) for _ in self.steps]

    def outputs(self):
        """(row, column) whose cell's rowspan is each bit of the product, least significant first."""
        return [(t + 1, f"g{t}.r{j}") for t in range(len(self.steps)) for j in self.observed[t]]

    def decode(self, xv, yv, layout):
        col = {name: i for i, (name, _) in enumerate(self.columns(xv, yv))}

        def rowspan_at(r, name):
            return next((h for c, h in zip(layout[r], self.program) if c == col[name]), None)

        return sum((rowspan_at(r, name) == 1) << i for i, (r, name) in enumerate(self.outputs()))

    def multiply(self, xv, yv):
        return self.decode(xv, yv, lay_out(self.rows(xv, yv)))

    def _free_counts(self):
        """Per repeated row, the fewest free columns over all inputs."""
        low = [None] * len(self.steps)
        for xv, yv in product(range(2 ** self.n), repeat=2):
            cov = []
            for r, row in enumerate(self.rows(xv, yv)):
                if r:
                    f = sum(1 for v in cov if v == 0)
                    low[r - 1] = f if low[r - 1] is None else min(low[r - 1], f)
                _, cov = place_row(cov, row)
        return low

    def _fill_spares(self):
        while True:
            short = [(r, len(self.program) - f) for r, f in enumerate(self._free_counts()) if f < len(self.program)]
            if not short:
                return
            r, k = short[0]
            self.spares += [(f"spare{r + 1}.{len(self.spares) + j}", r + 1) for j in range(k)]


if __name__ == "__main__":
    for n in [int(a) for a in sys.argv[1:]] or [2, 3]:
        c = Construction(n)
        wrong = [(x, y) for x, y in product(range(2 ** n), repeat=2) if c.multiply(x, y) != x * y]
        print(f"{n} x {n} bits: {4 ** n - len(wrong)} of {4 ** n} products right; {c.width()} columns, "
              f"{len(c.steps)} repeated rows of {len(c.program)} cells "
              f"(rowspan 1 at {[j for j, h in enumerate(c.program) if h == 1]})")

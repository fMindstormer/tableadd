"""Each position counts on its own: python research/positions.py

Let F_s(p) be the number of columns left of column p that are free in row s. In row s, the repeated row's
cells go to the free columns in order, so the free columns left of p are exactly the ones whose rank (the
number of free columns to their left) is below F_s(p). A column left of p is free in row s + 1 in exactly
one of three ways:

    it was free in row s and got the cell at its rank r with rowspan 1, or no cell (r >= the row's length k);
    it was free in row s + 1 - h, for some h >= 2, and got a cell of rowspan h there;
    its first-row cell has rowspan s + 1.

So, with q_r the rowspan of the repeated row's cell r,

    F_{s+1}(p) =  #{r < F_s(p) : r >= k or q_r = 1}
               +  sum over h >= 2 of #{r < min(F_{s+1-h}(p), k) : q_r = h}
               +  #{x < p : the first-row cell of column x has rowspan s + 1}.

Nothing else enters. The count at p is driven by its own past and by the first row left of p; it never sees
the count at any other position. A reader at p in row s learns F_s(p), its rank, and nothing more. So every
bit these tables compute is the end of one such chain, worked out from the first row alone; no result is
computed once and passed to two places. The right-hand side never decreases when an earlier F_s(p) grows,
which is why a gadget cannot pass on anything that falls as what it reads rises.

The count is not bounded by the length of the repeated row: columns past its last cell get no cell and stay
free. With the two cells <td rowspan="999"></td><td rowspan="1"></td> each row takes one free column away, so
a column that wakes in row t is free again in row t + 1 exactly when at least t columns were free to its left
in row 1. Put n input pairs to its left and it reads any threshold of the n bits; t = (n + 1)/2 is majority,
which no constant-depth, polynomial-size circuit of AND, OR and NOT gates computes.
"""
import random
import sys
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tableadd.table import place_row  # noqa: E402

H = 999


def free_left(first, program, rows):
    """F[s][p] for s = 1 .. rows: free columns left of column p in row s, from the forming algorithm."""
    cov, F = [], {}
    for s, row in enumerate([first] + [program] * rows):
        if s:
            F[s] = [sum(1 for x in range(p) if cov[x] == 0) for p in range(len(first) + 1)]
        _, cov = place_row(cov, row)
    return F


def predicted(first, program, F, s, p):
    """F_s(p) from the recurrence, using only F at p in earlier rows and the first row left of p."""
    k = len(program)
    stay = sum(1 for r in range(F[s - 1][p]) if r >= k or program[r] == 1)
    wake = sum(1 for h in range(2, s) for r in range(min(F[s - h][p], k)) if program[r] == h)
    ends = sum(1 for x in range(p) if first[x] == s)
    return stay + wake + ends


def check(tables=3000, seed=1):
    rng = random.Random(seed)
    checked = wrong = 0
    for _ in range(tables):
        first = [rng.choice([1, 2, 3, 4, 5, 6, H]) for _ in range(rng.randrange(3, 16))]
        program = [rng.choice([1, 1, 2, 3, H]) for _ in range(rng.randrange(1, 8))]
        rows = rng.randrange(2, 10)
        F = free_left(first, program, rows)
        for s in range(2, rows + 1):
            for p in range(len(first) + 1):
                checked += 1
                wrong += predicted(first, program, F, s, p) != F[s][p]
    return checked, wrong


def threshold(xs, t):
    """Lay out the threshold table for bits xs with the two-cell row; is the reader free again in row t + 1?"""
    n = len(xs)
    first = [1 if x else H for x in xs] + [t] + [H if x else 1 for x in reversed(xs)]
    cov = []
    for row in [first] + [[H, 1]] * t:
        _, cov = place_row(cov, row)
    return cov[n] == 0


if __name__ == "__main__":
    checked, wrong = check()
    print(f"recurrence against the forming algorithm, 3000 random tables: {checked} (row, position) checks, "
          f"{wrong} wrong")
    for n in (3, 5, 7, 9):
        bad = sum(threshold(xs, (n + 1) // 2) != (2 * sum(xs) > n) for xs in product((0, 1), repeat=n))
        print(f"majority of {n} bits with the row 999, 1: wrong on {bad} of {2 ** n} inputs")

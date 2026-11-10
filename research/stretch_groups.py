"""Which permutations of chain states can a fixed repeated row make? python research/stretch_groups.py [--search]

research/fixed_row.py keeps a bit in two states of the reader's chain that a stretch of rows can swap. With
five such states, and stretches whose permutations generate A5 (a step reads one bit and does one of two
permutations, both stretches of the same length), Barrington's theorem would give every NC1 function, every
bit of a product included, with one fixed row and polynomial-size tables. This file is about whether that is
possible.

The chain's state is its last D counts, D the largest rowspan below 999 in the row, and two states are
unordered when neither has at least as many free columns as the other in all D rows. Two runs fed the same
input that are ordered stay ordered, so a stretch that maps a set of states onto itself can only permute
unordered ones nontrivially.

1. One returning rowspan. Let every cell of the row have rowspan 1, h or 999. Then
       F_{s+1} = A(F_s) + B(F_{s+1-h}) + e,
   with A and B non-decreasing. For two runs fed the same input, d = their difference: the new d is a term
   with the sign of the newest d (or 0) plus a term with the sign of the oldest (or 0), so its sign is one of
   those two or 0. Read the last h differences as a cycle. The new one takes the oldest one's place, next to
   the newest, so the cycle's number of sign changes (zeros skipped) never rises.

2. Rowspan 2. Let every cell have rowspan 1, 2 or 999, so D = 2. Two runs whose states are unordered have
   newest differences of one sign and the one before of the other. By 1, the next difference has one of those
   signs or is 0, and the runs stay unordered only if it has the sign opposite to the newest: whichever run
   is ahead changes every row. So, on a set of mutually unordered states, the runs' newest counts are all
   different and their order reverses every row. A stretch of L rows that maps the set onto itself therefore
   keeps that order (L even) or reverses it (L odd): it is the identity or one fixed reversal, decided by L
   alone, whatever its inputs. No input can steer it, so such a row cannot even keep one bit this way.

check() runs the step of 2 on every pair of states (counts up to 8) and input up to 3 for every row of up to
4 cells with rowspans 1, 2 and 999, and 1 on random runs of every row of up to 4 cells with one returning
rowspan.

--search (about 6 minutes): with up to 3 columns waking per row and at most 3 live columns more than the
    states start with, every row of up to 3 cells with rowspans 1 to 5 and 999, every cycle of 3 to 6 states
    under a constant input, every 3 of its states that are mutually unordered, and stretches of up to 8 rows:
    which rows swap two of the three and keep the third (an odd permutation; on 3 states, any group past
    rotations has one). Rows with one returning rowspan have none in 2082 such sets. Rows with two have some:
    999 2 4, 999 3 5, 999 4 2 and 999 5 3, the first within 6 rows. Then all 282 cycles of 5 mutually
    unordered states in those rows, stretches of up to 8 rows: only rotations.

Longer runs of the same searches find nothing more: 3 states with one returning rowspan up to 9 rows; cycles
of 4 and 5 states in rows of up to 3 cells up to 11 rows, and in 999 5 3 up to 14; cycles of 5 states in
every row of 4 cells with two or more returning rowspans up to 10. With rowspans up to 5, no constant input
has a cycle longer than 5, so these are all the cycles there are. So stretches have given rotations, and on 3
states reflections, nothing that would lead to A5.

Open: whether a row with one returning rowspan of 3 or more ever does more than rotate (1 alone does not
settle it: for a single sleeping column at different phases, every pair of states has exactly 2 sign changes),
and whether a row with two, which can reflect 3 states, can generate A5 on 5 or more, with longer stretches,
longer cycles (rowspans past 5) or sets that are not cycles.
"""
import random
import sys
from itertools import combinations, product

H = 999
EMAX = 3


def chain(program, vmax=64):
    """(D, step): the chain's state is its last D counts, newest first."""
    k = len(program)
    hs = sorted({q for q in program if q not in (1, H)})
    A = [sum(1 for r in range(f) if r >= k or program[r] == 1) for f in range(vmax)]
    B = [(h - 1, [sum(1 for r in range(min(f, k)) if program[r] == h) for f in range(vmax)]) for h in hs]

    def step(s, e):
        return (A[s[0]] + sum(b[s[i]] for i, b in B) + e,) + s[:-1]
    return max(hs, default=1), step


def le(a, b):
    return all(p <= q for p, q in zip(a, b))


def unordered(a, b):
    return not le(a, b) and not le(b, a)


def sign_changes(d):
    s = [x for x in d if x]
    return sum(1 for a, b in zip(s, s[1:] + s[:1]) if (a > 0) != (b > 0)) if s else 0


def check():
    cases = 0
    for k in range(2, 5):
        for prog in product([1, 2, H], repeat=k):
            if 2 not in prog:
                continue
            _, step = chain(prog)
            states = list(product(range(9), repeat=2))
            for x, y, e in product(states, states, range(EMAX + 1)):
                x2, y2 = step(x, e), step(y, e)
                assert not (le(x, y) and not le(x2, y2)), (prog, x, y, e)
                if unordered(x, y) and unordered(x2, y2):
                    assert (x2[0] > y2[0]) != (x[0] > y[0]), (prog, x, y, e)
                cases += 1
    print(f"rowspans 1, 2, 999: {cases} (pair, input) cases; unordered runs swap the lead every row")
    rng, steps = random.Random(1), 0
    for k in range(2, 5):
        for prog in product([1, 2, 3, 4, 5, H], repeat=k):
            if len({c for c in prog if c not in (1, H)}) != 1:
                continue
            D, step = chain(prog)
            for _ in range(40):
                x, y = (tuple(rng.randrange(6) for _ in range(D)) for _ in range(2))
                for _ in range(30):
                    e = rng.randrange(EMAX + 1)
                    x2, y2 = step(x, e), step(y, e)
                    if max(x2 + y2) > 60:
                        break
                    assert sign_changes([a - b for a, b in zip(x2, y2)]) <= \
                        sign_changes([a - b for a, b in zip(x, y)]), (prog, x, y, e)
                    x, y, steps = x2, y2, steps + 1
    print(f"one returning rowspan: {steps} random steps of two runs; the cyclic sign changes never rose")


def live(program):
    """Live columns of a state: free now, or asleep on a cell placed in the last rows and not back yet."""
    k = len(program)
    hs = sorted({q for q in program if q not in (1, H)})
    cnt = {h: [sum(1 for r in range(min(f, k)) if program[r] == h) for f in range(64)] for h in hs}
    return lambda s: s[0] + sum(cnt[h][s[j]] for h in hs for j in range(1, min(h, len(s))))


def cycles(program, box, sizes):
    """Cycles of a constant input whose states have counts up to box."""
    D, step = chain(program)
    states = list(product(range(box + 1), repeat=D))
    out = set()
    for e in range(EMAX + 1):
        img = {}
        for s in states:
            t = step(s, e)
            img[s] = t if max(t) <= box else None
        done = set()
        for s0 in states:
            path, pos, s = [], {}, s0
            while s is not None and s not in done and s not in pos:
                pos[s] = len(path)
                path.append(s)
                s = img[s]
            if s is not None and s in pos and len(path) - pos[s] in sizes:
                out.add(tuple(path[pos[s]:]))
            done.update(path)
    return sorted(out)


def permutations(program, X, Lmax, slack=3):
    """Every permutation of X that a stretch of up to Lmax rows makes: BFS over the runs from all of X."""
    _, step = chain(program)
    m = live(program)
    top = max(m(s) for s in X) + slack
    index = {s: i for i, s in enumerate(X)}
    frontier, out = {tuple(X)}, set()
    for _ in range(Lmax):
        nxt = set()
        for imgs in frontier:
            for e in range(EMAX + 1):
                t = tuple(step(s, e) for s in imgs)
                if all(m(s) <= top for s in t):
                    nxt.add(t)
        frontier = nxt
        out |= {tuple(index[s] for s in t) for t in frontier if all(s in index for s in t) and len(set(t)) == len(t)}
    return out


def odd(p):
    return sum(1 for i, j in combinations(range(len(p)), 2) if p[i] > p[j]) % 2


def rotations(n):
    return {tuple((i + r) % n for i in range(n)) for r in range(n)}


def search(Lmax=8):
    rows = [p for k in (2, 3) for p in product([1, 2, 3, 4, 5, H], repeat=k)
            if H in p and any(c not in (1, H) for c in p)]
    for returning in (1, 2):
        found, tested = set(), 0
        for prog in rows:
            if len({c for c in prog if c not in (1, H)}) != returning:
                continue
            for cyc in cycles(prog, len(prog) + 2, range(3, 7)):
                for X in combinations(cyc, 3):
                    if all(unordered(a, b) for a, b in combinations(X, 2)):
                        tested += 1
                        if any(odd(p) for p in permutations(prog, list(X), Lmax)):
                            found.add(prog)
        print(f"rows with {returning} returning rowspan(s): {tested} sets of 3 states; rows with a stretch of up "
              f"to {Lmax} rows that swaps two and keeps the third: {sorted(found) or 'none'}", flush=True)
    beyond, tested = [], 0
    for prog in rows:
        for cyc in cycles(prog, len(prog) + 2, {5}):
            if all(unordered(a, b) for a, b in combinations(cyc, 2)):
                tested += 1
                order = list(cyc)                 # in the cycle's own order, the constant input rotates it
                if not permutations(prog, order, Lmax) <= rotations(5):
                    beyond.append(prog)
    print(f"{tested} cycles of 5 mutually unordered states; rows where a stretch of up to {Lmax} rows does more "
          f"than rotate them: {beyond or 'none'}", flush=True)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--search"]:
        search()
    else:
        check()

"""Every formula with one fixed repeated row: python research/barrington.py [--search]

Every repeated row is the same three cells, whatever the formula:

    <td rowspan="999"></td><td rowspan="2"></td><td rowspan="6"></td>

As in research/fixed_row.py, the reader learns only F_s, the number of free columns to its left in row s, and
with this row

    F_{s+1} = max(F_s - 3, 0) + [F_{s-1} >= 2] + [F_{s-5} >= 3] + e:

of the free columns, the first gets the 999 and is gone, the second sleeps one row, the third five, and the rest
stay free. The state is the last six counts, newest first. With e = 1 in every row and four live columns, the
count is 3 in every sixth row and 2 in the others: the state goes round the six rotations of (3, 2, 2, 2, 2, 2),
the 3 one place further back each row. Take five of them, all but the one with the 3 fourth:

    X0 = (3, 2, 2, 2, 2, 2)   X1 = (2, 3, 2, 2, 2, 2)   X2 = (2, 2, 3, 2, 2, 2)
    X3 = (2, 2, 2, 2, 3, 2)   X4 = (2, 2, 2, 2, 2, 3)

They are mutually unordered, and stretches of rows permute them. These three, for example (e row by row),

    10 rows  0121111111       (X0 X3 X2)(X1 X4)
    11 rows  12111110111      (X0 X4 X3 X2 X1)
    14 rows  01210121111111   (X0 X2 X3)

generate every permutation of the five: the stretches make the whole symmetric group S5. Its subgroup A5 is
not solvable, so Barrington's theorem applies. A formula of depth d (counting ANDs and ORs) becomes a program
of at most 4^d instructions, each "if x then g, else nothing" with g a 3-cycle of the five states:

    x            one instruction;
    NOT f        f's program for g^-1, then g;
    f AND f'     with g = [h1, h2] for 3-cycles h1, h2 (every 3-cycle is one), the programs of f for h1, f' for
                 h2, f for h1^-1 and f' for h2^-1: if either is false, the four cancel;
    f OR f'      NOT (NOT f AND NOT f').

An instruction is two stretches of the same length, a if x = 1 and b if x = 0, such that a then b^-1 makes g,
followed by a stretch that makes b^-1 whatever the input. Neighbouring constant stretches merge into the
shortest one that makes their product. With stretches of up to 30 rows, every 3-cycle has such a pair, of 15
to 24 rows, and every permutation a constant stretch, of at most 53 rows. As in research/fixed_row.py, each
row's e is written into the first row: constants as cells of rowspan s, x as a cell of rowspan s if x = 1 and
999 if x = 0 (or the other way round, for an e that falls when x rises).

Six rows with e = 2 2 1 1 1 2 bring the chain to X0, whose count is 3. The program's product is a 3-cycle that
moves X0 to a state with count 2 if the formula holds, and the identity if it doesn't. In the last row the
reader's own column is free at last and gets the cell of rank F: the rowspan-6 cell if the count is 2, none if
it is 3. The run lays every table out with the forming algorithm and reads the answer off for every input.

So a formula of depth d takes at most 77 * 4^d + 6 repeated rows (24 for an instruction's pair, 53 for the
constant after it), and about as many columns. Every function in NC1, every bit of the product of two n-bit
numbers among them, has formulas of depth O(log n), so tables of size polynomial in n compute it, all with
this one repeated row. The 999 has to be more than the number of rows; tables of 999 rows or more here use
65534, the largest rowspan HTML has. rowspan="0", which the specification lets grow to the end of the row
group, would keep one row for every n; that hasn't been checked here.

--search (about 6 hours of CPU; an hour and a half on 10 cores): which other rows of 3 cells do the same. For
every row of 999 and two different rowspans from 2 to 7, in any order: every cycle of 5 or more states under
e = 1 (states reached from the empty table with at most 3 columns waking per row and at most 6 live columns),
every 5 of its states that are mutually unordered, and every stretch of up to 12 rows that keeps the five runs
mutually unordered (once two runs are ordered they stay ordered, so they can never come back to the five) and
at most 3 live columns above where they started. It prints the largest group the stretches generate on any five
states.

Twelve of the 90 rows give A5 or S5 on some five states with stretches of up to 12 rows, all with 999 first and
a cell of rowspan 6 or 7: S5 in 999 2 6, 999 3 7, 999 4 6, 999 6 2, 999 6 4 and 999 7 3, A5 in 999 2 7,
999 3 6, 999 5 7, 999 6 3, 999 7 2 and 999 7 5. In 27 more the stretches make only a group of order 5, and in
the other 51 no cycle has five mutually unordered states. (In 999 3 7 it gave up on 42 of the 147 sets, with
more than 100000 joint states open.)
"""
import heapq
import sys
from itertools import combinations, product
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fixed_row  # noqa: E402
from positions import free_left  # noqa: E402
from stretch_groups import EMAX, H, chain, le, live  # noqa: E402

PROGRAM = [H, 2, 6]
X = tuple(tuple(3 if j == i else 2 for j in range(6)) for i in (0, 1, 2, 4, 5))
ID = tuple(range(5))


# --- permutations of states ---------------------------------------------------------------------------------

def comp(a, b):
    """First a, then b."""
    return tuple(b[a[i]] for i in range(len(a)))


def inv(p):
    q = [0] * len(p)
    for i, j in enumerate(p):
        q[j] = i
    return tuple(q)


def cycle_type(p):
    seen, out = set(), []
    for i in range(len(p)):
        n, j = 0, i
        while j not in seen:
            seen.add(j)
            j, n = p[j], n + 1
        if n > 1:
            out.append(n)
    return tuple(sorted(out))


def cycles_of(p, names):
    seen, out = set(), []
    for i in range(len(p)):
        if i in seen or p[i] == i:
            continue
        c, j = [], i
        while j not in seen:
            seen.add(j)
            c.append(names[j])
            j = p[j]
        out.append("(" + " ".join(c) + ")")
    return "".join(out) or "()"


def group(gens, n):
    G, frontier = {tuple(range(n))}, [tuple(range(n))]
    while frontier:
        nxt = []
        for g in frontier:
            for h in gens:
                x = comp(g, h)
                if x not in G:
                    G.add(x)
                    nxt.append(x)
        frontier = nxt
    return G


def antichain(states):
    return not any(le(a, b) or le(b, a) for a, b in combinations(states, 2))


def stretches(program, S, Lmax, slack=3, cap=None):
    """{L: {permutation: word}}: one input word for each permutation of S that a stretch of L <= Lmax rows makes.
    Breadth first over the runs from all of S at once, pruned as in --search. cap: give up (None) when more
    than cap joint states are open."""
    _, step = chain(program)
    m = live(program)
    loss = program.count(H)
    index = {s: i for i, s in enumerate(S)}
    top = max(m(s) for s in S)
    frontier, out = {tuple(S): ()}, {}
    for L in range(1, Lmax + 1):
        rem = Lmax - L
        nxt = {}
        for runs, word in frontier.items():
            for e in range(EMAX + 1):
                t = tuple(step(s, e) for s in runs)
                if t in nxt or any(m(s) > top + slack or m(s) - loss * rem > top for s in t) or not antichain(t):
                    continue
                nxt[t] = word + (e,)
        frontier = nxt
        if cap is not None and len(frontier) > cap:
            return None
        for t, word in frontier.items():
            if all(s in index for s in t):
                out.setdefault(L, {}).setdefault(tuple(index[s] for s in t), word)
    return out


def prefix(program, target, mmax=8):
    """The shortest input word from the empty table to target."""
    D, step = chain(program)
    m = live(program)
    parent, frontier = {(0,) * D: None}, [(0,) * D]
    while target not in parent:
        nxt = []
        for s in frontier:
            for e in range(EMAX + 1):
                t = step(s, e)
                if t not in parent and m(t) <= mmax:
                    parent[t] = (s, e)
                    nxt.append(t)
        frontier = nxt
    word, s = [], target
    while parent[s] is not None:
        s, e = parent[s]
        word.append(e)
    return tuple(reversed(word))


def by_layout(word):
    """The reader's last six counts after word, from the forming algorithm: the first row is e cells of rowspan
    s for each row s, then the reader."""
    first = [s for s, e in enumerate(word, 1) for _ in range(e)] + [H]
    F = free_left(first, PROGRAM, len(word))
    return tuple(F[s][len(first) - 1] if s >= 1 else 0 for s in range(len(word), len(word) - 6, -1))


# --- formulas -----------------------------------------------------------------------------------------------

class FormulaTable(fixed_row.Table):
    PROGRAM, READ = PROGRAM, {(6,): 1, (): 0}

    def __init__(self, start, stretches):
        self.START = start
        rows = len(start) + sum(len(next(iter(w.values()))) for _, w in stretches)
        self.H = H if rows < H else 65534
        assert rows < self.H
        self.PROGRAM = [self.H, 2, 6]
        super().__init__(stretches)


class Compiler:
    def __init__(self, Lmax=30):
        self.byL = stretches(PROGRAM, X, Lmax)
        edges = [(p, w) for d in self.byL.values() for p, w in d.items()]
        self.const, heap = {ID: ()}, [(0, ID)]          # the shortest constant stretch for each permutation
        while heap:
            n, p = heapq.heappop(heap)
            if n > len(self.const[p]):
                continue
            for q, w in edges:
                r, cand = comp(p, q), self.const[p] + w
                if r not in self.const or len(cand) < len(self.const[r]):
                    self.const[r] = cand
                    heapq.heappush(heap, (len(cand), r))
        self.C3 = sorted(p for p in self.const if cycle_type(p) == (3,))
        self.leaf = {}
        for g in self.C3:
            for L in sorted(self.byL):
                d = self.byL[L]
                pairs = [(a, b) for a in d for b in d if comp(a, inv(b)) == g]
                if pairs:
                    a, b = min(pairs, key=lambda ab: len(self.const[inv(ab[1])]))
                    self.leaf[g] = (d[a], d[b], inv(b))
                    break
        cost = {g: len(w1) + len(self.const[tail]) for g, (w1, _, tail) in self.leaf.items()}
        self.split = {g: min(((h1, h2) for h1 in self.C3 for h2 in self.C3
                              if comp(comp(comp(h1, h2), inv(h1)), inv(h2)) == g),
                             key=lambda h: cost[h[0]] + cost[h[1]] + cost[inv(h[0])] + cost[inv(h[1])])
                      for g in self.C3}
        self.start = prefix(PROGRAM, X[0])
        self.tops = [g for g in self.C3 if X[g[0]][0] == 2]      # 3-cycles taking X0 to a count of 2

    def program(self, f, g):
        """[('x', name, w1, w0) or ('c', permutation)]: product g if f holds, the identity if not."""
        if f[0] == 'x':
            w1, w0, tail = self.leaf[g]
            return [('x', f[1], w1, w0), ('c', tail)]
        if f[0] == 'not':
            return self.program(f[1], inv(g)) + [('c', g)]
        if f[0] == 'and':
            h1, h2 = self.split[g]
            return (self.program(f[1], h1) + self.program(f[2], h2) + self.program(f[1], inv(h1)) +
                    self.program(f[2], inv(h2)))
        if f[0] == 'or':
            return self.program(('not', ('and', ('not', f[1]), ('not', f[2]))), g)
        raise ValueError(f[0])

    def table(self, f):
        """The shortest of the tables for f, one for each 3-cycle the output can be."""
        best = min((self.parts(f, g) for g in self.tops), key=lambda ps: sum(len(next(iter(w.values())))
                                                                              for _, w in ps))
        return FormulaTable(self.start, best)

    def parts(self, f, top):
        parts, acc = [], ID
        for item in self.program(f, top) + [('c', ID)]:
            if item[0] == 'c':
                acc = comp(acc, item[1])
                continue
            if acc != ID:
                parts.append(((), {(): self.const[acc]}))
                acc = ID
            parts.append(((item[1],), {(1,): item[2], (0,): item[3]}))
        if acc != ID:
            parts.append(((), {(): self.const[acc]}))
        return parts


def value(f, v):
    if f[0] == 'x':
        return v[f[1]]
    if f[0] == 'not':
        return 1 - value(f[1], v)
    a, b = value(f[1], v), value(f[2], v)
    return a & b if f[0] == 'and' else a | b


def x(i):
    return ('x', f"x{i}")


FORMULAS = {
    "x0 AND x1": ('and', x(0), x(1)),
    "x0 XOR x1": ('or', ('and', x(0), ('not', x(1))), ('and', ('not', x(0)), x(1))),
    "(x0 AND x1) OR (x2 AND NOT x3)": ('or', ('and', x(0), x(1)), ('and', x(2), ('not', x(3)))),
    "majority of x0, x1, x2": ('or', ('or', ('and', x(0), x(1)), ('and', x(1), x(2))), ('and', x(0), x(2))),
}


# --- the search ---------------------------------------------------------------------------------------------

def reachable(program, mmax):
    D, step = chain(program)
    m = live(program)
    seen, frontier = {(0,) * D}, [(0,) * D]
    while frontier:
        nxt = []
        for s in frontier:
            for e in range(EMAX + 1):
                t = step(s, e)
                if m(t) <= mmax + 2 and t not in seen:
                    seen.add(t)
                    nxt.append(t)
        frontier = nxt
    return {s for s in seen if m(s) <= mmax}


def cycles(program, states):
    """The cycles of e = 1 through the given states, each in its own order."""
    _, step = chain(program)
    out, done = set(), set()
    for s0 in sorted(states):
        path, pos, s = [], {}, s0
        while s not in done and s not in pos and len(path) < 400:
            pos[s] = len(path)
            path.append(s)
            s = step(s, 1)
        if s in pos:
            c = path[pos[s]:]
            i = c.index(min(c))
            out.add(tuple(c[i:] + c[:i]))
        done.update(path)
    return sorted(out)


def largest_group(program, k=5, Lmax=12, mmax=6, cap=100000):
    best, sets, gave_up = 0, 0, 0
    for c in cycles(program, reachable(program, mmax)):
        for S in combinations(c, k):
            if not antichain(S):
                continue
            sets += 1
            found = stretches(program, list(S), Lmax, cap=cap)
            if found is None:
                gave_up += 1
                continue
            best = max(best, len(group([p for d in found.values() for p in d], k)))
    return program, sets, gave_up, best


def search():
    rows = [p for p in product([1, 2, 3, 4, 5, 6, 7, H], repeat=3)
            if H in p and len({c for c in p if c not in (1, H)}) == 2]
    found = {}
    with Pool() as pool:
        for program, sets, gave_up, best in pool.imap_unordered(largest_group, rows):
            found[program] = best
            if best >= 60:
                print(f"{' '.join(map(str, program))}: {sets} sets of 5 states ({gave_up} given up), "
                      f"largest group {best}", flush=True)
    print(f"{len(rows)} rows; with A5 or S5 on five states: "
          f"{sum(b >= 60 for b in found.values())}; largest groups otherwise: "
          f"{sorted({b for b in found.values() if b < 60})}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--search"]:
        search()
        sys.exit()
    names = [f"X{i}" for i in range(5)]
    _, step = chain(PROGRAM)
    assert antichain(X) and all(step(X[i], 1) == X[i + 1] for i in (0, 1, 3))
    cp = Compiler()
    found = {p: w for L in sorted(cp.byL, reverse=True) for p, w in cp.byL[L].items()}   # shortest last wins
    shortest = {}
    for p, w in found.items():
        t = cycle_type(p)
        if t not in shortest or len(w) < len(shortest[t][1]):
            shortest[t] = (p, w)
    G = group(list(found), 5)
    print(f"{' '.join(map(str, PROGRAM))}: stretches of up to 30 rows make {len(found)} permutations of the five "
          f"states, which generate a group of order {len(G)}")
    for t in sorted(shortest, key=lambda t: len(shortest[t][1])):
        p, w = shortest[t]
        print(f"  {len(w):2} rows  {''.join(map(str, w)):30} {cycles_of(p, names)}")
    starts = {a: prefix(PROGRAM, a) for a in X}
    checked = 0
    for L, d in cp.byL.items():
        for p, w in d.items():
            for i, a in enumerate(X):
                assert by_layout(starts[a] + w) == X[p[i]], (w, i)
                checked += 1
    print(f"every one of these stretches, from each of the five states: {checked} runs, each laid out with the "
          f"forming algorithm, all as the chain says")
    for name, f in FORMULAS.items():
        t = cp.table(f)
        wrong = sum(t.read(v) != value(f, v) for v in t.inputs())
        print(f"{name}: {len(t.inputs())} inputs, {wrong} wrong; {t.width()} columns ({len(t.spares)} spare), "
              f"{t.R} repeated rows, rowspan {t.H} for 'never'", flush=True)

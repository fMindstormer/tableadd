"""Two natural ways to build a binary counter from identical rows, and why neither can work.

Fact used by both: inside a group of columns, positions don't matter. A column's future depends only on its
own remaining rowspan and on the rowspan it gets when free, which depends only on how many free columns lie
to its left. So a group is described by the multiset of its columns' remaining rowspans, and the only thing
it shows the columns to its right is how many of its columns are free.

1. Synchronous: program period p; every cell keeps its free count = 0 (mod p) except in one decision row,
   where a 0-bit adds one. Then in the decision row each cell starts its count at z = (number of 0-bits to its
   left) mod p, and z == 0 is exactly the carry. It fails: a 1-bit cell's free count is a multiple of p, so
   the program cells it receives are whole periods, the same multiset whatever z is, and its future cannot
   depend on z. A 1-bit cell cannot see the carry, and making it count anything else puts every cell's
   position into everyone's count.

2. Wave: cells sleep except two rows per cycle: the row their left neighbour fires (they listen) and the row
   they fire. Only one pair of cells is awake at a time, so a listener counts exactly its neighbour's free
   columns. It fails: a firing cell's columns receive a prefix of the program, which may not contain 1 (that
   would wake them in a row where they must sleep), so the 1 that signals a carry must sit at or beyond the
   largest emission, and every entry below it is the 'sleep one cycle' value. A smaller (no-carry) emission
   starts the listening window earlier, which only ever trades entries for that sleep value; so both bit
   states move their count of sleeping columns the same way, while flipping a bit needs opposite directions.
   (Proved for columns that wake only on those two rows; the search below also allows skipping whole cycles.)

This file runs exhaustive searches over small designs of both kinds; both find nothing.
"""
import itertools
import sys


def sync_cycle(G, T, t, z):
    p = len(G); t = list(t); frees = []
    for r in range(T):
        k = z if r == 0 else 0
        nxt, n = [], 0
        for c in t:
            if c > 0: nxt.append(c - 1)
            else: nxt.append(G[(k + n) % p] - 1); n += 1
        frees.append(n); t = nxt
    return frees, tuple(t)


def sync_search(p, T, w, vmax):
    found = 0
    for G in itertools.product(range(1, vmax + 1), repeat=p):
        if len(set(G)) == 1: continue
        info = {}
        for t in itertools.product(range(vmax), repeat=w):
            res = [sync_cycle(G, T, t, z) for z in range(p)]
            if any(f % p for fr, _ in res for f in fr[1:]): continue
            f0 = res[0][0][0] % p
            if f0 in (0, 1): info[t] = (1 - f0, [nt for _, nt in res])
        S = set(info)
        changed = True
        while changed:
            changed = False
            for t in list(S):
                b, nx = info[t]
                if any(nx[z] not in S or info[nx[z]][0] != b ^ (z == 0) for z in range(p)):
                    S.discard(t); changed = True
        found += bool(S and {info[t][0] for t in S} == {0, 1})
    return found


def wave_cell(G, T, s, e_in, maxskip):
    nxt, fire, k = [], [], e_in
    for i, o in enumerate(s):
        if o == 0:
            if k >= len(G): return None
            v = G[k]; k += 1
            if v == 1: fire.append(i); nxt.append(None)
            else:
                c, r = divmod(v, T)
                if r not in (0, 1) or not 1 <= c <= maxskip: return None
                nxt.append(2 * (c - 1) + r)
        elif o == 1: fire.append(i); nxt.append(None)
        else: nxt.append(o - 2)
    for rank, i in enumerate(fire):
        if rank >= len(G): return None
        c, r = divmod(G[rank] + 1, T)
        if r not in (0, 1) or not 1 <= c <= maxskip: return None
        nxt[i] = 2 * (c - 1) + r
    return len(fire), tuple(nxt)


def wave_search(T, w, K, maxskip):
    vals = sorted({1} | {c * T + r for c in range(1, maxskip + 1) for r in (0, 1)} |
                  {c * T + r - 1 for c in range(1, maxskip + 1) for r in (0, 1)})
    states = list(itertools.product(range(2 * maxskip), repeat=w))
    found = 0
    for G in itertools.product(vals, repeat=K):
        clocks = {}
        for wc in range(1, 4):
            for sc in itertools.product(range(2 * maxskip), repeat=wc):
                r = wave_cell(G, T, sc, 0, maxskip)
                if r and r[1] == sc and r[0] > 0: clocks.setdefault(r[0], sc)
        if not clocks: continue
        tab = {(s, e): wave_cell(G, T, s, e, maxskip) for s in states for e in range(w + 2)}
        for s0, s1 in itertools.permutations(states, 2):
            for ec in clocks:
                E1, E0, ok = {ec}, set(), True
                for _ in range(8):
                    n1, n0 = set(E1), set(E0)
                    for b, s in ((0, s0), (1, s1)):
                        for c, Ec in ((0, E0), (1, E1)):
                            for e in Ec:
                                r = tab.get((s, e))
                                if r is None or r[1] != (s1 if b ^ c else s0): ok = False; break
                                (n1 if b & c else n0).add(r[0])
                            if not ok: break
                        if not ok: break
                    if not ok or n1 & n0: ok = False; break
                    if (n1, n0) == (E1, E0): break
                    E1, E0 = n1, n0
                if ok: found += 1; break
    return found


if __name__ == "__main__":
    for args in [(2, 3, 4, 4), (3, 3, 4, 4), (3, 2, 5, 3), (4, 3, 5, 4)]:
        print(f"synchronous p={args[0]} T={args[1]} width={args[2]} rowspans<={args[3]}: {sync_search(*args)} designs")
        sys.stdout.flush()
    for args in [(3, 3, 6, 1), (4, 3, 6, 1), (5, 3, 6, 1), (4, 3, 5, 2)]:
        print(f"wave T={args[0]} width={args[1]} program length={args[2]} skip<={args[3]}: {wave_search(*args)} designs")
        sys.stdout.flush()

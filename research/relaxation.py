"""Survey: what do identical rows do on their own? For every program (a short repeated sequence of rowspans,
period 2 to 5, rowspans 1 to 4; one per rotation class) start from a random first row and check whether the
layout becomes periodic in time. Information in a table only travels rightward, so disturbances drift off the
right edge; every program settles."""
import itertools
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tableadd.table import place_row  # noqa: E402


def settles(G, first, rows=260, width=200, window=40, max_period=12):
    cov, seen = [], []
    prog = list(G) * (len(first) // len(G) + 2)
    for r in range(rows):
        cols, nxt = place_row(cov, first if r == 0 else prog)
        line = [0] * width
        for x in range(min(width, len(cov))):
            if cov[x] > 0: line[x] = -1
        for x, h in zip(cols, first if r == 0 else prog):
            if x < width: line[x] = h
        seen.append(tuple(line)); cov = nxt
    return next((t for t in range(1, max_period + 1)
                 if all(seen[-1 - i] == seen[-1 - i - t] for i in range(window))), None)


if __name__ == "__main__":
    rng = random.Random(1)
    first = [rng.randint(1, 4) for _ in range(300)]
    reps, keys = [], set()
    for p in range(2, 6):
        for G in itertools.product(range(1, 5), repeat=p):
            if len(set(G)) == 1: continue
            key = min(G[i:] + G[:i] for i in range(p))
            if key not in keys:
                keys.add(key); reps.append(key)
    periods = [settles(G, first) for G in reps]
    print(f"{len(reps)} programs; periodic after 260 rows: {sum(t is not None for t in periods)}; "
          f"longest period: {max(t for t in periods if t)}")

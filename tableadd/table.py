"""The HTML table forming algorithm (WHATWG HTML, "forming a table"), for cells with colspan 1.

Each row places its cells in order: a cell goes to the first slot, from the left, that no cell from an earlier
row still covers, then the cursor moves one column on. A cell with rowspan h covers its column for h rows.
With colspan 1 two cells can never overlap, so this is the whole algorithm, with no error cases in which
browsers could differ.

A cell with rowspan="0" grows downward: in standards mode (a page with <!doctype html>) the specification makes
it cover its column in every later row of its row group, and every table here is one row group, so it never
frees its column.

cov[x] = how many more rows column x stays covered by cells placed in earlier rows (0 = free)."""

GROWS = float("inf")    # cov of a column under a cell with rowspan 0


def place_row(cov, rowspans):
    """Place one row. Returns (columns, next_cov): columns[i] = the column cell i lands in."""
    cov = list(cov)
    nxt = [c - 1 if c > 0 else 0 for c in cov]
    x, cols = 0, []
    for h in rowspans:
        while x < len(cov) and cov[x] > 0:
            x += 1
        if x >= len(cov):
            cov.extend([0] * (x + 1 - len(cov)))
            nxt.extend([0] * (x + 1 - len(nxt)))
        cols.append(x)
        nxt[x] = h - 1 if h else GROWS
        x += 1
    return cols, nxt


def lay_out(table):
    """table: list of rows, each a list of rowspans. Returns, per row, the column of each cell."""
    cov, out = [], []
    for row in table:
        cols, cov = place_row(cov, row)
        out.append(cols)
    return out

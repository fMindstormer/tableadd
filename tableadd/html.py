"""HTML for an adder table. The rows after the first are the same string, byte for byte."""
from .adder import PROGRAM, H, bits, columns

SUBSCRIPT = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def table(x, y, n, carry_in=0, style="plain", tid=None, invert_b=False):
    """The table that adds x + y (+ carry_in) in n bits; with invert_b, x + NOT y (+ carry_in).

    style 'plain':  rowspans only, nothing else.
    style 'readme': text marks for places that keep rowspan but strip scripts, styles and classes, such as a
                    GitHub README. Each input bit is written in the column of its pair that wakes (a₀=1 or
                    a₀=0), the sum and carry-out columns are labelled, and a repeated-row cell with rowspan 1
                    shows an orange square. Bit i of the sum is the first cell under its label s<i>.
    """
    a, b = bits(x, n), bits(y, n)
    cols = columns(a, b, carry_in, invert_b)
    idattr = f' id="{tid}"' if tid else ""
    if style == "plain":
        first = "".join(f'<td rowspan="{h}"></td>' for _, h in cols)
        prog = "".join(f'<td rowspan="{h}"></td>' for h in PROGRAM)
        return f"<table{idattr}><tr>{first}</tr>" + f"<tr>{prog}</tr>" * n + "</table>"
    if style == "readme":
        def first_cell(name, h):
            base, _, tail = name.partition(".")
            kind = base.rstrip("0123456789")
            i = base[len(kind):]
            text = ""
            if kind in ("a", "b") and h != H:
                text = f"{kind}{i.translate(SUBSCRIPT)}={'0' if tail == 'not' else '1'}"
            elif kind == "sum" and not tail:
                text = f"s{i.translate(SUBSCRIPT)}"
            elif kind == "carry" and int(i) == n - 1:
                text = f"c{str(n).translate(SUBSCRIPT)}"
            return f'<td rowspan="{h}">{text}</td>'
        first = "".join(first_cell(name, h) for name, h in cols)
        prog = "".join(f'<td rowspan="{h}">{"🟧" if h == 1 else ""}</td>' for h in PROGRAM)
        # one <tr> per line, so the source shows the repeated row as repeated lines
        return f"<table{idattr}>\n<tr>{first}</tr>\n" + f"<tr>{prog}</tr>\n" * n + "</table>"
    raise ValueError(f"unknown style {style!r}")

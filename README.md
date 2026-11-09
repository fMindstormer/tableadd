# tableadd

**An HTML table that adds two binary numbers.** After the first row, every row is the same line of HTML,
and your browser works out the sum while it lays the table out. The only rule involved is how HTML places a
row's cells around taller cells from the rows above. There is no JavaScript and no CSS.

![The table adding 11 + 6 in Chromium: a readout says 11 + 6 = 17, read from the layout, above a table of
narrow columns where orange and dark cells form a staircase](docs/example.png)

*11 + 6 in Chromium, from the [demo page](docs/index.html). Blue and green are the bits of a and b, each
written in the column of its pair that becomes free; purple is the carry in. The orange and dark cells come
from the repeated rows: orange cells have rowspan 1, dark ones rowspan 999. The ringed cells are the answer,
read from where the browser put them: under s0 to s3, orange is 1 and dark is 0, and an orange ring under c4
is the carry out.*

## It runs on this page

GitHub strips scripts and styles from a README but keeps `rowspan`, so the table below is laid out, and the
sum worked out, by your browser as you read this. It adds 3 + 3:

<table>
<tr><td rowspan="999"></td><td rowspan="1">a₀=1</td><td rowspan="1">b₀=1</td><td rowspan="1"></td><td rowspan="1"></td><td rowspan="2">a₁=1</td><td rowspan="2">b₁=1</td><td rowspan="2">c₂</td><td rowspan="2">c₂</td><td rowspan="2">s₁</td><td rowspan="2"></td><td rowspan="2"></td><td rowspan="2"></td><td rowspan="999"></td><td rowspan="999"></td><td rowspan="1">s₀</td><td rowspan="1"></td><td rowspan="1"></td><td rowspan="1"></td><td rowspan="999"></td><td rowspan="999"></td><td rowspan="1"></td><td rowspan="1"></td></tr>
<tr><td rowspan="999"></td><td rowspan="999"></td><td rowspan="999"></td><td rowspan="1">🟧</td><td rowspan="999"></td><td rowspan="1">🟧</td><td rowspan="999"></td><td rowspan="999"></td><td rowspan="999"></td><td rowspan="999"></td></tr>
<tr><td rowspan="999"></td><td rowspan="999"></td><td rowspan="999"></td><td rowspan="1">🟧</td><td rowspan="999"></td><td rowspan="1">🟧</td><td rowspan="999"></td><td rowspan="999"></td><td rowspan="999"></td><td rowspan="999"></td></tr>
</table>

Under s₀ and s₁, the first cell is that bit of the sum: 🟧 for 1, empty for 0. A 🟧 under either c₂ is the
carry out. Read from c₂ to s₀, the table says 110: six. The last two lines of its source are the same.

## How it works

### One rule

HTML's [table forming algorithm](https://html.spec.whatwg.org/multipage/tables.html#forming-a-table) places
each row's cells from left to right, each in the first slot that no taller cell from an earlier row still
covers. Every cell here is one column wide, so cells never overlap, and the specification leaves an engine
no choice: every cell has exactly one slot it can go to.

In each row, a free column learns one number: how many free columns lie to its left, because that decides
which of the row's cells lands on it. So the repeated row is a lookup table from that number to a rowspan:

```html
<tr><td rowspan="999"></td><td rowspan="999"></td><td rowspan="999"></td><td rowspan="1"></td><td rowspan="999"></td><td rowspan="1"></td><td rowspan="999"></td><td rowspan="999"></td><td rowspan="999"></td><td rowspan="999"></td></tr>
```

A free column with 3 or 5 free columns to its left gets a cell one row tall, so it is free again in the next
row. Every other free column gets a cell that covers it to the bottom of the table.

### A bit is a pair of columns

Counting the first row as row 0, the first row decides when each column first becomes free: a column under a
first-row cell with rowspan *r* is free in row *r*. Bit *i* of a number is a pair of columns. The left one becomes free in row *i* + 1 if the
bit is 1, and never otherwise; the right one the other way round. So in that row exactly one of the two is
free, and everything outside the pair counts it as one free column either way. Only columns between the two
count the bit.

The first row is therefore the circuit with the inputs plugged in. It fixes the order of the columns and when
each wakes; only the rowspans of the input pairs depend on the numbers, and the sum appears nowhere in it.

### A full adder is six readers inside three pairs

Full adder *i* works in row *i* + 1. Its columns, from left to right:

```
a=1  b=1  R1 R2  [full adder i + 1]  R3 R4 R5 R6  b=0  a=0
```

`a=1` and `a=0` are the two columns of *a*'s pair, named for the value that frees them. The six readers wake
in row *i* + 1 inside the pairs for *a* and *b* and inside the carry's pair, so reader R*j* finds
*s* + *j* − 1 free columns to its left, where *s* = *a* + *b* + carry. The repeated row answers each of them:

| Reader | Free again in the next row when | So it means |
|---|---|---|
| R1 | *s* = 3 | carry |
| R2 | *s* = 2 | carry |
| R3 | *s* is odd | the sum bit is 1 |
| R4 | *s* is even | the sum bit is 0 |
| R5 | *s* = 1 | no carry |
| R6 | *s* = 0 | no carry |

Full adder *i* + 1 sits between R2 and R3, so in its row it counts R1 and R2, exactly one of which is free
when there is a carry. The nesting is the wiring. R1 or R2 on the left and R5 or R6 on the right make the
carry a pair like the others, so the block counts the same to everything on its right whatever the carry.
The carry in is a pair at the two ends of the table, and one spare column at the right end fills row 1, so
every repeated row finds exactly ten free columns and no cell spills past the right edge.

Adding two *n*-bit numbers takes 10*n* + 3 columns and *n* repeated rows. The [code](tableadd/adder.py) is
the same construction in Python, with the forming algorithm in [`tableadd/table.py`](tableadd/table.py).

### Subtraction and comparison are the adder rewired

Swapping the two columns of a pair inverts its bit: the left one is then the one that wakes when the bit is 0.
So the adder with *b*'s pairs swapped and the carry in tied to 1 works out *a* + NOT *b* + 1 = *a* − *b* +
2<sup>*n*</sup>. The sum bits are *a* − *b* modulo 2<sup>*n*</sup>, and the carry out is 1 exactly when
*a* ≥ *b*. Only the order of the first row's columns changes, and the repeated rows are the same. The table
for *a* − *b* is, byte for byte, the table for *a* + (2<sup>*n*</sup> − 1 − *b*) with a carry in, so the
engine checks below have already laid out every four-bit subtraction.

## Where it works

| Engine | What it is | Result |
|---|---|---|
| Chromium 141 | Blink, the engine in Chrome and Edge | every cell in its slot |
| Firefox 159 | Gecko, on macOS | every cell in its slot |
| Safari 27.0.1 | WebKit, in Safari itself on macOS | every cell in its slot |
| WebKitGTK 2.52.6 | WebKit, the engine Safari is built on, in its Linux port | every cell in its slot |
| wkhtmltopdf 0.12.6 | a WebKit from 2016 (AppleWebKit/602.1) in an HTML-to-PDF tool | every cell in its slot |
| WeasyPrint 70 | an HTML-to-PDF tool with its own layout engine, written in Python | every cell in its slot |

Each engine laid out all 512 four-bit tables (every *a* and *b*, with and without a carry in), 200 random
eight-bit tables and 60 random twelve-bit tables. The check compares the column of every cell with the
specification's algorithm, not just the answer, and then reads the sum from the engine's layout.

The [demo page](docs/index.html) measures the layout in whichever browser opens it and says whether the sum
it read matches *a* + *b*, so opening it checks any other browser.

## Multiplication

The same rule multiplies. Every row after the first is still one repeated line of HTML, but unlike the
adder's, that line gets longer as the numbers get wider.

[`research/product_scan.py`](research/product_scan.py) multiplies two *n*-bit numbers column by column. A
count, the carry plus the partial products *a*<sub>*i*</sub>*b*<sub>*j*</sub> of the current column added so
far, is passed from gadget to gadget the way the adder passes its carry, one partial product per row. What a
gadget passes on is the number of free columns left of the next one, which is how many of the repeated row's
cells from its first up to the gadget's last left reader have rowspan 1. So it never falls as the number of
free columns the gadget finds to its left rises, and no single row can add *xy* to a count *T*:
*T* + *xy* is not a non-decreasing function of any weighted sum of *T*, *x* and *y*. It takes two halves. A
row reads *x* and *y*, each written *m* + 1 times, and passes on *T* + *xy* + *m*(*x* + *y*), where *m*
bounds *T*; the next row takes *m*(*x* + *y*) away by reading NOT *x* and NOT *y*, written *m* times each,
along with its own inputs. A column's last partial product is added and halved in one row, and the reader
after that row's window gives the column's bit of the product, as R3 does in the adder. The repeated row is
a block of 999s and two patterns of 1s, one for each kind of row.

| Bits | Columns | Repeated rows | Cells in the repeated row |
|---|---|---|---|
| 2 × 2 | 53 | 5 | 10 |
| 3 × 3 | 269 | 10 | 31 |
| 4 × 4 | 695 | 17 | 50 |

Every product is right in the specification's algorithm (all 16, 64 and 256), and Safari 27.0.1 places every
cell where the specification does in all 64 three-bit tables and in 16 random four-bit ones. The other
engines haven't been run on the multipliers yet, and Safari is slow on tables this wide. The tables
are less tidy than the adder: some consumed columns stay free instead of being covered for good, and spare
columns at the right end keep every row at least as wide as the repeated row.
[`research/multiply.py`](research/multiply.py) is an earlier two-bit version built by hand, 75 columns and 4
repeated rows of 17 cells: one row fewer than the general one, but wider.

## What I found on the way

I first tried to make the repeated rows count, like a clock. That failed, and why it failed led to the adder.

- **Identical rows forget.** Take a repeated row that is itself a short pattern: two to five cells over and
  over, rowspans one to four (296 patterns, counting rotations once). Every one of them turns a random first
  row into a layout that repeats every 12 rows or fewer by row 260
  ([`research/relaxation.py`](research/relaxation.py)). A column's fate depends only on the columns to its
  left, so information only travels rightward, and disturbances drift off the edge.
- **A group of columns shows one number.** Order inside a group doesn't matter: its future depends only on
  its columns' remaining rowspans, and all it shows the columns to its right is how many of them are free.
- **Two natural counters are impossible.** [`research/no_counter.py`](research/no_counter.py) has both
  proofs and exhaustive searches over small designs of each kind, which find none.
  - *Synchronous:* if each bit is a group of columns whose free count is a multiple of the repeated row's
    period except in one row, a group holding a 1 receives whole periods of the row, the same cells in some
    order whatever the carry, so it can't see the carry.
  - *A wave,* where columns wake in turn and each listens to its left neighbour: both states of a bit can
    only move the count the same way, and flipping a bit needs both ways (proved for columns that wake only
    to listen and to answer).
- **Pairs fix it.** A pair counts as one free column to everything outside it, so a bit can be read without
  moving anything else. The price is the shape: a reader has to sit inside every pair it reads, so
  information only flows inward, from the outside of the nest to its middle.
- **Each position counts on its own.** Take the number of free columns left of some column in a row. In the
  next row it is how many of them landed on a cell of rowspan 1 or past the repeated row's last cell, where
  they get no cell and stay free, plus the columns left of it whose longer cells from earlier rows end, plus
  first-row cells that end. Nothing else enters
  ([`research/positions.py`](research/positions.py) has the proof and checks it on 3000 random tables). A
  reader learns only its own count, so every bit is the end of one such chain worked out from the first row,
  and no result is computed once and passed to two places. The count never falls when an earlier one
  rises, which is why adding a partial product takes two rows. Nor is it bounded by the row's length: with
  the two cells `<td rowspan="999"></td><td rowspan="1"></td>`, a column that wakes in row *t* is free in
  row *t* + 1 exactly when at least *t* of the input bits to its left are 1, so a two-cell row computes
  majority.

## What came before

- **Computing in HTML and CSS.** The best-known example, Rule 110 in HTML and CSS (Eli Fox-Epstein, 2011),
  advances only while someone clicks or presses keys. Here nothing is clicked and there is no CSS: the page is
  laid out once.
- **Table layout as a hard problem.** Research on table layout is about choosing column widths: Anderson and
  Sobti showed it NP-hard for tables of text, and Gange, Marriott, Stuckey and Moulder solved it exactly. This
  table uses only the step before that, assigning cells to slots, which the specification fixes exactly; that
  is why every engine agrees.
- I found no earlier table that computes with `rowspan`.

## Run it

```sh
python -m tableadd 173 85 --bits 8 > table.html    # the table for 173 + 85
python -m tableadd 3 3 --bits 2 --style readme     # with marks, as in this README
python -m tableadd 173 85 --bits 8 --sub           # 173 − 85, and whether 173 ≥ 85

pip install -r requirements.txt && playwright install chromium
python -m pytest tests                  # the spec's algorithm on many sums, then the engines
python tests/engines.py 8 200           # 200 random 8-bit tables in every engine installed
python research/relaxation.py           # identical rows forget
python research/no_counter.py           # the two counters that can't work
python research/positions.py            # each position counts on its own; majority in two cells
python research/product_scan.py 2 3 4   # multipliers for 2, 3 and 4 bits, every product
python research/multiply.py             # the two-bit special case
python tools/picture.py 11 6 4          # docs/example.png
```

`python -m tableadd` writes the table to standard output and the sum it reads back from the layout to
standard error; with `--sub`, the difference, signed by the carry out.

WebKitGTK runs through the system Python (Ubuntu: `apt install gir1.2-webkit2-4.1 xvfb`), and wkhtmltopdf
with poppler's `pdftotext`; engines that are missing are skipped. On macOS, `tests/engines.py` also opens a
tab in Firefox and in Safari, on a page served from 127.0.0.1 that sends back where every cell landed. The
pytest suite leaves them out, so it doesn't open browser windows. The package itself has no dependencies.

[`docs/index.html`](docs/index.html) is the demo page, a single file: open it, or serve `docs/` with GitHub
Pages.

## Next

- One row for every width: which functions can a fixed repeated row compute? While a count is below the
  row's length, the row can send it through any staircase that rises by 0 or 1 at a time; past that, it
  takes off the same amount whatever the count. My guess is that no fixed row multiplies numbers of every
  width, because the middle bits of a product need a count of up to about *n* partial products; inner
  product mod 2 is the cleanest case to try to prove. (This item used to say that a fixed row computes only
  AC⁰. That assumed a count stays below the row's length, and majority, above, shows it doesn't.)
- Computing without a bound: in Rule 110, cells exchange results. Here no position ever sees another's;
  each runs its own count over the first row to its left. I expect identical rows can't compute without a
  bound in that sense, but the question needs a precise statement first.
- Smaller, tidier multipliers: about a third of each one's columns are readers that only carry a window
  from one pattern of the repeated row to the other, and a tenth are spare columns.

## License

MIT, Fedir Yudin.

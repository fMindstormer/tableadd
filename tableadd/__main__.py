"""python -m tableadd A B [--bits N] [--carry | --sub] [--style plain|readme]

Writes the adder table as HTML to stdout and prints, on stderr, the sum read back from the layout that the
specification's algorithm gives (tableadd.table). With --sub the table is the adder with B's pairs swapped and
carry in 1, and stderr has A - B, signed by the carry out."""
import argparse
import sys

from .adder import add, subtract
from .html import table


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tableadd", description=__doc__.splitlines()[0])
    ap.add_argument("a", type=int)
    ap.add_argument("b", type=int)
    ap.add_argument("--bits", type=int, default=8)
    op = ap.add_mutually_exclusive_group()
    op.add_argument("--carry", action="store_true", help="carry in")
    op.add_argument("--sub", action="store_true", help="a - b: the adder reading NOT b, with carry in 1")
    ap.add_argument("--style", choices=("plain", "readme"), default="plain")
    args = ap.parse_args(argv)
    if not (0 <= args.a < 2 ** args.bits and 0 <= args.b < 2 ** args.bits):
        ap.error(f"a and b must fit in {args.bits} bits")
    if args.sub:
        sys.stdout.write(table(args.a, args.b, args.bits, 1, style=args.style, invert_b=True) + "\n")
        diff, geq = subtract(args.a, args.b, args.bits)
        signed = diff if geq else diff - 2 ** args.bits
        print(f"{args.a} - {args.b} = {signed} (read from the layout; carry out {int(geq)}, so a "
              f"{'>=' if geq else '<'} b)", file=sys.stderr)
        return
    sys.stdout.write(table(args.a, args.b, args.bits, int(args.carry), style=args.style) + "\n")
    got = add(args.a, args.b, args.bits, int(args.carry))
    print(f"{args.a} + {args.b}{' + 1' if args.carry else ''} = {got} (read from the layout)", file=sys.stderr)


if __name__ == "__main__":
    main()

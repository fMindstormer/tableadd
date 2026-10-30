"""python -m tableadd A B [--bits N] [--carry] [--style plain|readme]

Writes the adder table as HTML to stdout and prints, on stderr, the sum read back from the layout that the
specification's algorithm gives (tableadd.table)."""
import argparse
import sys

from .adder import add
from .html import table


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tableadd", description=__doc__.splitlines()[0])
    ap.add_argument("a", type=int)
    ap.add_argument("b", type=int)
    ap.add_argument("--bits", type=int, default=8)
    ap.add_argument("--carry", action="store_true", help="carry in")
    ap.add_argument("--style", choices=("plain", "readme"), default="plain")
    args = ap.parse_args(argv)
    if not (0 <= args.a < 2 ** args.bits and 0 <= args.b < 2 ** args.bits):
        ap.error(f"a and b must fit in {args.bits} bits")
    sys.stdout.write(table(args.a, args.b, args.bits, int(args.carry), style=args.style) + "\n")
    got = add(args.a, args.b, args.bits, int(args.carry))
    print(f"{args.a} + {args.b}{' + 1' if args.carry else ''} = {got} (read from the layout)", file=sys.stderr)


if __name__ == "__main__":
    main()

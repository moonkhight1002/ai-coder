from __future__ import annotations

import sys


def solve(data: str) -> str:
    """
    Sample solution for the included demo problem.

    Problem format:
    - first integer: n
    - next n integers: values to sum

    Replace this implementation when solving a different problem.
    """
    tokens = data.split()
    if not tokens:
        return ""

    n = int(tokens[0])
    numbers = [int(value) for value in tokens[1 : 1 + n]]
    return str(sum(numbers))


if __name__ == "__main__":
    sys.stdout.write(solve(sys.stdin.read()))

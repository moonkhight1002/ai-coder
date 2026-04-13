from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROBLEMS_DIR = ROOT / "problems"
SOLUTION_FILE = ROOT / "solution.py"


def normalize_output(text: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(line.rstrip() for line in lines)


def discover_problem(arg: str | None) -> Path:
    if arg:
        candidate = Path(arg)
        if not candidate.is_absolute():
            candidate = PROBLEMS_DIR / arg
        if candidate.is_file():
            return candidate.parent
        if candidate.is_dir():
            return candidate
        raise FileNotFoundError(f"Problem path not found: {arg}")

    directories = sorted(path for path in PROBLEMS_DIR.iterdir() if path.is_dir())
    if not directories:
        raise FileNotFoundError("No problem directories found under problems/.")
    if len(directories) == 1:
        return directories[0]

    preferred = PROBLEMS_DIR / "sample_sum"
    if preferred.exists():
        return preferred

    raise RuntimeError(
        "Multiple problem directories found. Pass one explicitly, for example: "
        "python test_runner.py sample_sum"
    )


def load_tests(problem_dir: Path) -> list[dict[str, str]]:
    tests_file = problem_dir / "tests.json"
    with tests_file.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError("tests.json must contain a list of test cases.")
    return payload


def run_case(case: dict[str, str], timeout_seconds: int = 5) -> tuple[bool, str]:
    process = subprocess.run(
        [sys.executable, str(SOLUTION_FILE)],
        input=case["input"],
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        cwd=str(ROOT),
    )

    actual = normalize_output(process.stdout)
    expected = normalize_output(case["expected"])

    if process.returncode != 0:
        message = process.stderr.strip() or f"Non-zero exit code: {process.returncode}"
        return False, message

    if actual != expected:
        return False, f"expected={expected!r}, actual={actual!r}"

    return True, "ok"


def main() -> int:
    if not PROBLEMS_DIR.exists():
        print("Missing problems/ directory.")
        return 1
    if not SOLUTION_FILE.exists():
        print("Missing solution.py.")
        return 1

    problem_arg = sys.argv[1] if len(sys.argv) > 1 else None
    problem_dir = discover_problem(problem_arg)
    tests = load_tests(problem_dir)

    print(f"Running {len(tests)} test(s) for {problem_dir.name}")

    failures = 0
    for index, case in enumerate(tests, start=1):
        ok, detail = run_case(case)
        label = case.get("name", f"case_{index}")
        if ok:
            print(f"[PASS] {label}")
        else:
            failures += 1
            print(f"[FAIL] {label}: {detail}")

    if failures:
        print(f"\n{failures} test(s) failed.")
        return 1

    print("\nAll tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

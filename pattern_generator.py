import json
import copy


PATTERN_KINDS = ("cross", "x")


def generate_pattern(n: int, kind: str) -> list[list[int]]:
    kind = kind.lower()
    mid = n // 2
    rules = {
        "cross": lambda i, j: i == mid or j == mid,
        "x":     lambda i, j: i == j  or i + j == n - 1,
    }
    if kind not in rules:
        raise ValueError(f"지원하지 않는 패턴 종류: '{kind}'. 사용 가능: {PATTERN_KINDS}")
    fn = rules[kind]
    return [[1 if fn(i, j) else 0 for j in range(n)] for i in range(n)]


def _make_noisy(pattern: list[list[int]], positions: list[tuple], value: float) -> list[list[int]]:
    noisy = copy.deepcopy(pattern)
    for r, c in positions:
        noisy[r][c] = value
    return noisy


def build_data_json(filepath: str = "data.json", sizes: tuple = (5, 13, 25)) -> dict:
    data = {"filters": {}, "patterns": {}}

    for n in sizes:
        data["filters"][f"size_{n}"] = {kind: generate_pattern(n, kind) for kind in PATTERN_KINDS}

        for idx, (kind, expected, noisy_fn) in enumerate([
            ("cross", "+",  lambda p, n: _make_noisy(p, [(0, 0), (n-1, n-1)], 0.1)),
            ("x",     "x",  lambda p, n: _make_noisy(p, [(0, n//2), (n//2, 0)], 0.2)),
            ("cross", "+",  lambda p, n: _make_noisy(p, [(0, 0), (n-1, n-1)], 0.1)),
            ("x",     "x",  lambda p, n: _make_noisy(p, [(0, n//2), (n//2, 0)], 0.2)),
        ]):
            base = generate_pattern(n, kind)
            inp = base if idx % 2 == 0 else noisy_fn(base, n)
            data["patterns"][f"size_{n}_{idx}"] = {"input": inp, "expected": expected}

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    n_patterns = len(data["patterns"])
    print(f"  {filepath} 생성 완료 (패턴 {n_patterns}개)")
    return data

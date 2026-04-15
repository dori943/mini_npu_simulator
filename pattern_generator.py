import json
import copy

# 지원하는 패턴 종류
PATTERN_KINDS = ("cross", "x")


def generate_pattern(n: int, kind: str) -> list[list[int]]:
    """N×N 패턴 생성. kind: 'cross' | 'x'"""
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
    """패턴 복사 후 지정 좌표에 노이즈 값 삽입"""
    noisy = copy.deepcopy(pattern)
    for r, c in positions:
        noisy[r][c] = value
    return noisy


def build_data_json(filepath: str = "data.json", sizes: tuple = (5, 13, 25)) -> dict:
    """data.json 생성: 크기별 필터(cross/x) + 4종 패턴(완벽×2, 노이즈×2)"""
    data = {"filters": {}, "patterns": {}}

    for n in sizes:
        # 필터
        data["filters"][f"size_{n}"] = {kind: generate_pattern(n, kind) for kind in PATTERN_KINDS}

        # 패턴 4종
        for idx, (kind, expected, noisy_fn) in enumerate([
            ("cross", "+",  lambda p, n: _make_noisy(p, [(0, 0), (n-1, n-1)], 0.1)),
            ("x",     "x",  lambda p, n: _make_noisy(p, [(0, n//2), (n//2, 0)], 0.2)),
            ("cross", "+",  lambda p, n: _make_noisy(p, [(0, 0), (n-1, n-1)], 0.1)),  # 노이즈
            ("x",     "x",  lambda p, n: _make_noisy(p, [(0, n//2), (n//2, 0)], 0.2)),  # 노이즈
        ]):
            base = generate_pattern(n, kind)
            # 짝수 인덱스(0,2)는 완벽 패턴, 홀수(1,3)는 노이즈 패턴
            inp = base if idx % 2 == 0 else noisy_fn(base, n)
            data["patterns"][f"size_{n}_{idx}"] = {"input": inp, "expected": expected}

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    n_patterns = len(data["patterns"])
    print(f"  ✅ {filepath} 생성 완료 (패턴 {n_patterns}개)")
    return data

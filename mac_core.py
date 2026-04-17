"""MAC 연산 / 판정 / 성능 측정 / 검증"""

import time

EPSILON = 1e-9

LABEL_MAP = {
    "+": "Cross", "cross": "Cross", "Cross": "Cross", "CROSS": "Cross",
    "x": "X",     "X": "X",
}


def normalize_label(raw: str | None) -> str | None:
    if raw is None:
        return None
    return LABEL_MAP.get(raw) or LABEL_MAP.get(raw.strip().lower())


def mac(pattern: list, filt: list) -> float:
    n = len(pattern)
    return sum(pattern[i][j] * filt[i][j] for i in range(n) for j in range(n))


#모드1
def judge_ab(score_a: float, score_b: float) -> str:
    diff = score_a - score_b
    if abs(diff) < EPSILON:
        return "판정 불가"
    return "A" if diff > 0 else "B"


#모드2
def judge(score_cross: float, score_x: float) -> str:
    diff = score_cross - score_x
    if abs(diff) < EPSILON:
        return "UNDECIDED"
    return "Cross" if diff > 0 else "X"


def measure(pattern: list, filt: list, repeats: int = 10) -> tuple[float, float]:
    total_time = 0.0
    score = 0.0
    for _ in range(repeats):
        start_time = time.perf_counter()
        score = mac(pattern, filt)
        end_time = time.perf_counter()

        total_time += (end_time - start_time) * 1000
    
    avg_time = score, avg_time

    return score,avg_time


def validate_matrix(matrix: list, expected_size: int) -> tuple[bool, str]:
    if not isinstance(matrix, list):
        return False, "리스트가 아님"
    if len(matrix) != expected_size:
        return False, f"행 수 불일치: {len(matrix)} != {expected_size}"
    for i, row in enumerate(matrix):
        if not isinstance(row, list) or len(row) != expected_size:
            col_count = len(row) if isinstance(row, list) else "?"
            return False, f"{i}행 열 수 불일치: {col_count} != {expected_size}"
    return True, "OK"

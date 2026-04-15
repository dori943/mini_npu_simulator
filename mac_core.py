"""MAC 연산 / 판정 / 성능 측정 / 검증"""

import time

EPSILON = 1e-9

LABEL_MAP = {
    "+": "Cross", "cross": "Cross", "Cross": "Cross", "CROSS": "Cross",
    "x": "X",     "X": "X",
}


def normalize_label(raw: str | None) -> str | None:
    """다양한 형태의 라벨 → 표준 라벨(Cross/X)"""
    if raw is None:
        return None
    return LABEL_MAP.get(raw) or LABEL_MAP.get(raw.strip().lower())


def mac(pattern: list, filt: list) -> float:
    """MAC(Multiply-Accumulate) 연산: 위치별 곱의 합"""
    n = len(pattern)
    return sum(pattern[i][j] * filt[i][j] for i in range(n) for j in range(n))


def judge(score_cross: float, score_x: float) -> str:
    """점수 비교 → Cross / X / UNDECIDED"""
    diff = score_cross - score_x
    if abs(diff) < EPSILON:
        return "UNDECIDED"
    return "Cross" if diff > 0 else "X"


def measure(pattern: list, filt: list, repeats: int = 10) -> tuple[float, float]:
    """MAC 연산 반복 측정 → (점수, 평균 시간 ms)"""
    times = []
    score = 0.0
    for _ in range(repeats):
        t0 = time.perf_counter()
        score = mac(pattern, filt)
        times.append((time.perf_counter() - t0) * 1000)
    return score, sum(times) / len(times)


def validate_matrix(matrix: list, expected_size: int) -> tuple[bool, str]:
    """행렬 크기 검증 → (valid, 메시지)"""
    if not isinstance(matrix, list):
        return False, "리스트가 아님"
    if len(matrix) != expected_size:
        return False, f"행 수 불일치: {len(matrix)} != {expected_size}"
    for i, row in enumerate(matrix):
        if not isinstance(row, list) or len(row) != expected_size:
            col_count = len(row) if isinstance(row, list) else "?"
            return False, f"{i}행 열 수 불일치: {col_count} != {expected_size}"
    return True, "OK"

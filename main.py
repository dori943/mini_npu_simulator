"""
Mini NPU Simulator
- MAC(Multiply-Accumulate) 연산 시뮬레이터
- 모드 1: 사용자 입력(3×3), 모드 2: data.json 분석
"""

import json
import time
import os


# ============================================================
# 1. 패턴 생성기
# ============================================================

def generate_cross_pattern(n):
    """N×N 십자가(+) 패턴 생성"""
    pattern = []
    mid = n // 2
    for i in range(n):
        row = []
        for j in range(n):
            if i == mid or j == mid:
                row.append(1)
            else:
                row.append(0)
        pattern.append(row)
    return pattern


def generate_x_pattern(n):
    """N×N X 패턴 생성"""
    pattern = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j or i + j == n - 1:
                row.append(1)
            else:
                row.append(0)
        pattern.append(row)
    return pattern


# ============================================================
# 2. 라벨 정규화
# ============================================================

LABEL_MAP = {
    "+": "Cross",
    "cross": "Cross",
    "Cross": "Cross",
    "CROSS": "Cross",
    "x": "X",
    "X": "X",
}


def normalize_label(raw_label):
    """다양한 형태의 라벨을 표준 라벨(Cross/X)로 변환"""
    if raw_label is None:
        return None
    result = LABEL_MAP.get(raw_label, None)
    if result is None:
        result = LABEL_MAP.get(raw_label.strip().lower(), None)
    return result


# ============================================================
# 3. MAC 연산 (핵심)
# ============================================================

EPSILON = 1e-9


def mac_operation(pattern, filter_matrix):
    """
    MAC(Multiply-Accumulate) 연산
    같은 위치의 값을 곱하고 모두 더함
    """
    score = 0.0
    n = len(pattern)
    for i in range(n):
        for j in range(n):
            score += pattern[i][j] * filter_matrix[i][j]
    return score


# ============================================================
# 4. 점수 비교 및 판정
# ============================================================

def judge(score_cross, score_x):
    """
    두 필터의 MAC 점수를 비교하여 판정
    Returns: "Cross" / "X" / "UNDECIDED"
    """
    diff = score_cross - score_x
    if abs(diff) < EPSILON:
        return "UNDECIDED"
    elif diff > 0:
        return "Cross"
    else:
        return "X"


# ============================================================
# 5. 입력 검증
# ============================================================

def read_matrix(size, name="행렬"):
    """콘솔에서 N×N 행렬을 한 줄씩 입력받음 (검증 포함)"""
    print(f"\n[{name}] {size}x{size} 행렬을 한 줄씩 입력하세요 (공백 구분):")
    matrix = []

    for row_idx in range(size):
        while True:
            try:
                line = input(f"  {row_idx + 1}행: ").strip()
                if line == "":
                    print(f"  ⚠ 입력 형식 오류: 각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요.")
                    continue

                values = line.split()
                if len(values) != size:
                    print(f"  ⚠ 입력 형식 오류: 각 줄에 {size}개의 숫자를 "
                          f"공백으로 구분해 입력하세요. (현재 {len(values)}개)")
                    continue

                row = [float(v) for v in values]
                matrix.append(row)
                break

            except ValueError:
                print(f"  ⚠ 숫자 파싱 실패: 숫자만 입력하세요.")
                continue

    return matrix


def validate_matrix_size(matrix, expected_size):
    """행렬의 행/열 크기 검증"""
    if not isinstance(matrix, list):
        return False, "행렬이 리스트가 아닙니다"
    if len(matrix) != expected_size:
        return False, f"행 수 불일치: {len(matrix)} != {expected_size}"
    for i, row in enumerate(matrix):
        if not isinstance(row, list):
            return False, f"{i}행이 리스트가 아닙니다"
        if len(row) != expected_size:
            return False, f"{i}행 열 수 불일치: {len(row)} != {expected_size}"
    return True, "OK"


# ============================================================
# 6. 성능 측정
# ============================================================

def measure_mac_time(pattern, filter_matrix, repeats=10):
    """MAC 연산을 repeats회 반복 측정하여 (점수, 평균시간ms) 반환"""
    times = []
    result = 0.0

    for _ in range(repeats):
        start = time.perf_counter()
        result = mac_operation(pattern, filter_matrix)
        end = time.perf_counter()
        times.append((end - start) * 1000)

    avg_time = sum(times) / len(times)
    return result, avg_time


def print_performance_table(results):
    """
    성능 분석 표 출력
    results: [(size, avg_time_ms), ...]
    """
    print()
    print("=" * 58)
    print(" 성능 분석 (MAC 연산 시간, 10회 평균)")
    print("=" * 58)
    print(f"  {'크기(NxN)':<14}{'연산 횟수(N²)':<16}{'평균 시간(ms)':<16}")
    print("-" * 58)

    for size, avg_time in results:
        ops = size * size
        print(f"  {size}x{size:<10}  {ops:<16}{avg_time:<16.6f}")

    print("=" * 58)


# ============================================================
# 7. data.json 자동 생성
# ============================================================

def generate_data_json(filepath="data.json"):
    """data.json이 없을 경우 자동 생성"""
    sizes = [5, 13, 25]

    data = {
        "filters": {},
        "patterns": {}
    }

    # 필터 생성
    for n in sizes:
        data["filters"][f"size_{n}"] = {
            "cross": generate_cross_pattern(n),
            "x": generate_x_pattern(n)
        }

    # 패턴 생성
    pattern_idx = 0
    for n in sizes:
        # 완벽한 Cross 패턴
        data["patterns"][f"size_{n}_{pattern_idx}"] = {
            "input": generate_cross_pattern(n),
            "expected": "+"
        }
        pattern_idx += 1

        # 완벽한 X 패턴
        data["patterns"][f"size_{n}_{pattern_idx}"] = {
            "input": generate_x_pattern(n),
            "expected": "x"
        }
        pattern_idx += 1

        # 노이즈가 약간 있는 Cross 패턴
        noisy_cross = generate_cross_pattern(n)
        if n >= 5:
            noisy_cross[0][0] = 0.1
            noisy_cross[n - 1][n - 1] = 0.1
        data["patterns"][f"size_{n}_{pattern_idx}"] = {
            "input": noisy_cross,
            "expected": "+"
        }
        pattern_idx += 1

        # 노이즈가 약간 있는 X 패턴
        noisy_x = generate_x_pattern(n)
        if n >= 5:
            noisy_x[0][n // 2] = 0.2
            noisy_x[n // 2][0] = 0.2
        data["patterns"][f"size_{n}_{pattern_idx}"] = {
            "input": noisy_x,
            "expected": "x"
        }
        pattern_idx += 1

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"  ✅ {filepath} 자동 생성 완료 (패턴 {pattern_idx}개)")
    return data


# ============================================================
# 8. 모드 1: 사용자 입력 (3×3)
# ============================================================

def mode_1_user_input():
    """사용자가 3×3 필터 2개와 패턴 1개를 입력하여 판정"""
    SIZE = 3

    print()
    print("=" * 55)
    print(" 모드 1: 사용자 입력 (3x3)")
    print("=" * 55)

    # 필터 A (Cross) 입력
    print("\n--- 필터 A (예: 십자가 Cross) ---")
    print("  예시: 0 1 0 / 1 1 1 / 0 1 0")
    filter_a = read_matrix(SIZE, "필터 A")
    print(f"  ✅ 필터 A 저장 완료!")

    # 필터 B (X) 입력
    print("\n--- 필터 B (예: X자) ---")
    print("  예시: 1 0 1 / 0 1 0 / 1 0 1")
    filter_b = read_matrix(SIZE, "필터 B")
    print(f"  ✅ 필터 B 저장 완료!")

    # 패턴 입력
    print("\n--- 판별할 패턴 ---")
    pattern = read_matrix(SIZE, "패턴")
    print(f"  ✅ 패턴 저장 완료!")

    # MAC 연산 + 시간 측정
    print("\n--- MAC 연산 수행 중... ---")
    score_a, time_a = measure_mac_time(pattern, filter_a, repeats=10)
    score_b, time_b = measure_mac_time(pattern, filter_b, repeats=10)

    # 판정
    result = judge(score_a, score_b)

    # 결과 출력
    print()
    print("=" * 55)
    print(" 판정 결과")
    print("=" * 55)
    print(f"  필터 A(Cross) 점수  : {score_a}")
    print(f"  필터 A 연산 시간    : {time_a:.6f} ms")
    print(f"  필터 B(X) 점수      : {score_b}")
    print(f"  필터 B 연산 시간    : {time_b:.6f} ms")
    print(f"  ────────────────────────────")
    print(f"  판정 결과           : {result}")

    if result == "UNDECIDED":
        print(f"  → 두 필터의 점수가 동일하여 판정 불가")
    elif result == "Cross":
        print(f"  → 입력 패턴은 십자가(Cross)에 더 유사합니다!")
    else:
        print(f"  → 입력 패턴은 X자에 더 유사합니다!")

    print("=" * 55)

    # 성능 분석 표
    avg_time = (time_a + time_b) / 2
    print_performance_table([(SIZE, avg_time)])


# ============================================================
# 9. 모드 2: data.json 분석
# ============================================================

def extract_size_from_key(pattern_key):
    """
    패턴 키에서 크기(N)를 추출
    예: 'size_5_0' → 5, 'size_13_2' → 13
    """
    try:
        parts = pattern_key.split("_")
        # 'size', '{N}', '{idx}' 형태
        if len(parts) >= 2 and parts[0] == "size":
            return int(parts[1])
    except (ValueError, IndexError):
        pass
    return None


# ============================================================
# 9. 모드 2: data.json 분석 (패턴 순회부터)
# ============================================================

def mode_2_json_analysis():
    """data.json에서 필터와 패턴을 로드하여 일괄 판정"""

    filepath = "data.json"

    print()
    print("=" * 65)
    print(" 모드 2: data.json 분석")
    print("=" * 65)

    # ---- data.json 로드 또는 생성 ----
    if not os.path.exists(filepath):
        print(f"\n  ⚠ {filepath}이 없습니다. 자동 생성합니다...")
        data = generate_data_json(filepath)
    else:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"  ✅ {filepath} 로드 완료")
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON 파싱 오류: {e}")
            print(f"  → 파일을 재생성합니다...")
            data = generate_data_json(filepath)

    # ---- 최상위 스키마 검증 ----
    if "filters" not in data:
        print("  ❌ 'filters' 키가 없습니다. 분석을 중단합니다.")
        return
    if "patterns" not in data:
        print("  ❌ 'patterns' 키가 없습니다. 분석을 중단합니다.")
        return

    filters = data["filters"]
    patterns = data["patterns"]

    # ---- 결과 집계용 변수 ----
    total_cases = 0
    pass_count = 0
    fail_count = 0
    fail_details = []          # [(케이스키, 사유), ...]
    performance_data = {}      # {size: [(time_cross, time_x), ...]}

    # ---- 헤더 출력 ----
    print()
    print("-" * 72)
    print(f"  {'케이스':<16} {'Cross점수':<11} {'X점수':<11} {'판정':<11} {'expected':<10} {'결과':<6}")
    print("-" * 72)

    # ============================================================
    # 각 패턴 순회
    # ============================================================
    for p_key in sorted(patterns.keys()):
        total_cases += 1
        p_data = patterns[p_key]

        # ---- (1) 키에서 크기(N) 추출 ----
        size_n = extract_size_from_key(p_key)
        if size_n is None:
            fail_count += 1
            fail_details.append((p_key, "키에서 크기(N) 추출 실패"))
            print(f"  {p_key:<16} {'---':<11} {'---':<11} {'---':<11} {'---':<10} {'FAIL':<6}")
            continue

        # ---- (2) 해당 크기의 필터 찾기 ----
        filter_key = f"size_{size_n}"
        if filter_key not in filters:
            fail_count += 1
            fail_details.append((p_key, f"필터 '{filter_key}'가 존재하지 않음"))
            print(f"  {p_key:<16} {'---':<11} {'---':<11} {'---':<11} {'---':<10} {'FAIL':<6}")
            continue

        filter_set = filters[filter_key]

        # ---- (3) cross / x 필터 존재 확인 ----
        if "cross" not in filter_set:
            fail_count += 1
            fail_details.append((p_key, f"'{filter_key}'에 'cross' 필터 없음"))
            print(f"  {p_key:<16} {'---':<11} {'---':<11} {'---':<11} {'---':<10} {'FAIL':<6}")
            continue

        if "x" not in filter_set:
            fail_count += 1
            fail_details.append((p_key, f"'{filter_key}'에 'x' 필터 없음"))
            print(f"  {p_key:<16} {'---':<11} {'---':<11} {'---':<11} {'---':<10} {'FAIL':<6}")
            continue

        filter_cross = filter_set["cross"]
        filter_x = filter_set["x"]

        # ---- (4) input / expected 존재 확인 ----
        if "input" not in p_data:
            fail_count += 1
            fail_details.append((p_key, "'input' 필드 없음"))
            print(f"  {p_key:<16} {'---':<11} {'---':<11} {'---':<11} {'---':<10} {'FAIL':<6}")
            continue

        if "expected" not in p_data:
            fail_count += 1
            fail_details.append((p_key, "'expected' 필드 없음"))
            print(f"  {p_key:<16} {'---':<11} {'---':<11} {'---':<11} {'---':<10} {'FAIL':<6}")
            continue

        input_pattern = p_data["input"]
        raw_expected = p_data["expected"]

        # ---- (5) expected 라벨 정규화 ----
        expected_label = normalize_label(raw_expected)
        if expected_label is None:
            fail_count += 1
            fail_details.append((p_key, f"expected 라벨 정규화 실패: '{raw_expected}'"))
            print(f"  {p_key:<16} {'---':<11} {'---':<11} {'---':<11} {raw_expected:<10} {'FAIL':<6}")
            continue

        # ---- (6) 크기 검증: 입력 패턴 ----
        valid, msg = validate_matrix_size(input_pattern, size_n)
        if not valid:
            fail_count += 1
            fail_details.append((p_key, f"입력 패턴 크기 오류: {msg}"))
            print(f"  {p_key:<16} {'---':<11} {'---':<11} {'---':<11} {expected_label:<10} {'FAIL':<6}")
            continue

        # ---- (7) 크기 검증: Cross 필터 ----
        valid, msg = validate_matrix_size(filter_cross, size_n)
        if not valid:
            fail_count += 1
            fail_details.append((p_key, f"Cross 필터 크기 오류: {msg}"))
            print(f"  {p_key:<16} {'---':<11} {'---':<11} {'---':<11} {expected_label:<10} {'FAIL':<6}")
            continue

        # ---- (8) 크기 검증: X 필터 ----
        valid, msg = validate_matrix_size(filter_x, size_n)
        if not valid:
            fail_count += 1
            fail_details.append((p_key, f"X 필터 크기 오류: {msg}"))
            print(f"  {p_key:<16} {'---':<11} {'---':<11} {'---':<11} {expected_label:<10} {'FAIL':<6}")
            continue

        # ---- (9) MAC 연산 + 시간 측정 ----
        score_cross, time_cross = measure_mac_time(input_pattern, filter_cross, repeats=10)
        score_x, time_x = measure_mac_time(input_pattern, filter_x, repeats=10)

        # 성능 데이터 수집
        if size_n not in performance_data:
            performance_data[size_n] = []
        performance_data[size_n].append((time_cross + time_x) / 2)

        # ---- (10) 판정 ----
        judgment = judge(score_cross, score_x)

        # ---- (11) PASS / FAIL 비교 ----
        if judgment == expected_label:
            result_str = "PASS"
            pass_count += 1
        elif judgment == "UNDECIDED":
            # UNDECIDED는 어떤 expected와도 일치하지 않으므로 FAIL
            result_str = "FAIL"
            fail_count += 1
            fail_details.append((p_key, f"판정 UNDECIDED (expected: {expected_label})"))
        else:
            result_str = "FAIL"
            fail_count += 1
            fail_details.append((p_key, f"판정 {judgment} != expected {expected_label}"))

        # ---- (12) 행 출력 ----
        print(f"  {p_key:<16} {score_cross:<11.2f} {score_x:<11.2f} {judgment:<11} {expected_label:<10} {result_str:<6}")

    # ============================================================
    # 성능 분석 표 출력
    # ============================================================

    # 3×3도 성능 표에 포함 (패턴 생성기로 생성하여 측정)
    perf_results = []

    # 3×3 측정 추가
    cross_3 = generate_cross_pattern(3)
    filter_cross_3 = generate_cross_pattern(3)
    _, time_3 = measure_mac_time(cross_3, filter_cross_3, repeats=10)
    perf_results.append((3, time_3))

    # data.json에서 수집한 크기별 평균
    for size_n in sorted(performance_data.keys()):
        times = performance_data[size_n]
        avg = sum(times) / len(times)
        perf_results.append((size_n, avg))

    print_performance_table(perf_results)

    # ============================================================
    # 결과 리포트 (콘솔)
    # ============================================================

    print()
    print("=" * 65)
    print(" 결과 리포트")
    print("=" * 65)
    print(f"  전체 테스트 수 : {total_cases}")
    print(f"  통과 (PASS)    : {pass_count}")
    print(f"  실패 (FAIL)    : {fail_count}")

    if fail_count > 0:
        print()
        print("  --- 실패 케이스 목록 ---")
        for case_key, reason in fail_details:
            print(f"    ❌ {case_key}: {reason}")
    else:
        print()
        print("  🎉 모든 테스트를 통과했습니다!")
        print("  → 라벨 정규화(+→Cross, x→X)와 epsilon 비교 정책이")
        print("    올바르게 적용되어 0 FAIL을 달성했습니다.")

    print("=" * 65)


# ============================================================
# 10. 메인 함수
# ============================================================

def print_banner():
    """프로그램 시작 배너"""
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║        Mini NPU Simulator v1.0              ║")
    print("║   MAC 연산 기반 패턴 판별 시뮬레이터        ║")
    print("╚══════════════════════════════════════════════╝")
    print()


def main():
    print_banner()

    while True:
        print("실행 모드를 선택하세요:")
        print("  1) 사용자 입력 (3x3 필터/패턴 직접 입력)")
        print("  2) data.json 분석 (자동 일괄 판정)")
        print("  3) data.json 생성만 (파일 새로 생성)")
        print("  q) 종료")
        print()

        choice = input("선택 >>> ").strip()

        if choice == "1":
            mode_1_user_input()
            print()

        elif choice == "2":
            mode_2_json_analysis()
            print()

        elif choice == "3":
            generate_data_json("data.json")
            print()

        elif choice.lower() == "q":
            print("\n프로그램을 종료합니다. 수고하셨습니다! 👋")
            break

        else:
            print("⚠ 잘못된 입력입니다. 1, 2, 3, q 중 선택하세요.\n")


# ============================================================
# 실행
# ============================================================

if __name__ == "__main__":
    main()
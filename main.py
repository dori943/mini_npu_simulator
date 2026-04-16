import json
import os

from mac_core import normalize_label, measure, judge, validate_matrix
from pattern_generator import generate_pattern, build_data_json, PATTERN_KINDS


# 공통 UI
def print_banner():
    print()
    print("        Mini NPU Simulator v1.0              ")
    print("      MAC 연산 기반 패턴 판별 시뮬레이터        ")
    print()


def print_performance_table(results: list):
    print()
    print("=" * 55)
    print(" 성능 분석 (MAC 연산 시간, 10회 평균)")
    print("=" * 55)
    print(f"  {'크기(NxN)':<14}{'연산 횟수':<16}{'평균 시간(ms)'}")
    print("-" * 55)
    for size, avg in results:
        print(f"  {size}x{size:<10}  {size*size:<16}{avg:.6f}")
    print("=" * 55)


def read_matrix(size: int, name: str = "행렬") -> list:
    """N×N 행렬 입력 (오류 시 재입력)"""
    print(f"\n[{name}] {size}x{size} 입력 (공백 구분):")
    matrix = []
    for i in range(size):
        while True:
            try:
                values = input(f"  {i+1}행: ").strip().split()
                if len(values) != size:
                    print(f"  {size}개 숫자를 공백으로 구분해 입력하세요. (현재 {len(values)}개)")
                    continue
                matrix.append([float(v) for v in values])
                break
            except ValueError:
                print("  숫자만 입력하세요.")
    return matrix


def read_binary_matrix(size: int, name: str = "행렬") -> list:
    """N×N 이진 행렬 입력 - 0과 1만 허용 (오류 시 재입력)"""
    print(f"\n[{name}] {size}x{size} 입력 (0 또는 1만, 공백 구분):")
    matrix = []
    for i in range(size):
        while True:
            try:
                values = input(f"  {i+1}행: ").strip().split()
                if len(values) != size:
                    print(f"  {size}개 숫자를 공백으로 구분해 입력하세요. (현재 {len(values)}개)")
                    continue
                row = [int(v) for v in values]
                if any(v not in (0, 1) for v in row):
                    print(f"  0 또는 1만 입력하세요. (입력값: {row})")
                    continue
                matrix.append(row)
                break
            except ValueError:
                print("  0 또는 1 정수만 입력하세요.")
    return matrix


# 모드 1: 사용자 입력 (3×3)
def mode_1_user_input():
    SIZE = 3
    print("\n" + "=" * 55)
    print(" 모드 1: 사용자 입력 (3x3)")
    print("=" * 55)

    filters = []
    for name, hint in [("필터 A", "예: 0 1 0 / 1 1 1 / 0 1 0"),
                       ("필터 B", "예: 1 0 1 / 0 1 0 / 1 0 1")]:
        print(f"\n--- {name} ({hint}) ---")
        filters.append(read_binary_matrix(SIZE, name))
        print(f"  {name} 저장 완료")

    pattern = read_binary_matrix(SIZE, "패턴")
    print("  패턴 저장 완료")

    scores, times = [], []
    for filt in filters:
        s, t = measure(pattern, filt)
        scores.append(s)
        times.append(t)

    result = judge(scores[0], scores[1])

    print("\n" + "=" * 55)
    print(" 판정 결과")
    print("=" * 55)
    for label, score, t in zip(["A(Cross)", "B(X)"], scores, times):
        print(f"  필터 {label} 점수 : {score}  ({t:.6f} ms)")
    print("  ────────────────────────────────────────")
    print(f"  판정 결과     : {result}")
    msgs = {
        "UNDECIDED": "두 필터 점수 동일, 판정 불가",
        "Cross":     "입력 패턴은 십자가(Cross)에 더 유사합니다!",
        "X":         "입력 패턴은 X자에 더 유사합니다!",
    }
    print(f"  → {msgs[result]}")
    print("=" * 55)

    print_performance_table([(SIZE, sum(times) / len(times))])


# 모드 2: data.json 분석
def _extract_size(key: str):
    try:
        parts = key.split("_")
        if len(parts) >= 2 and parts[0] == "size":
            return int(parts[1])
    except (ValueError, IndexError):
        pass
    return None


def _fail(p_key: str, expected: str, reason: str, fail_list: list) -> None:
    """FAIL 행 출력 + fail_list 추가"""
    print(f"  {p_key:<16} {'---':<11} {'---':<11} {'---':<11} {expected:<10} FAIL")
    fail_list.append((p_key, reason))


def _load_json(filepath: str) -> dict:
    """JSON 로드, 실패 시 자동 생성"""
    if not os.path.exists(filepath):
        print(f" {filepath} 없음. 자동 생성합니다...")
        return build_data_json(filepath)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f" {filepath} 로드 완료")
        return data
    except json.JSONDecodeError as e:
        print(f" JSON 파싱 오류: {e}. 재생성합니다...")
        return build_data_json(filepath)


def mode_2_json_analysis():
    """data.json 필터/패턴 일괄 판정 + 성능 분석"""
    print("\n" + "=" * 65)
    print(" 모드 2: data.json 분석")
    print("=" * 65)

    data = _load_json("data.json")
    if "filters" not in data or "patterns" not in data:
        print(" 'filters' 또는 'patterns' 키 없음. 분석 중단.")
        return

    filters, patterns = data["filters"], data["patterns"]
    total = passed = failed = 0
    fail_list = []
    perf = {}  # {size: [avg_ms, ...]}

    print()
    print("-" * 72)
    print(f"  {'케이스':<16} {'Cross점수':<11} {'X점수':<11} {'판정':<11} {'expected':<10} {'결과':<6}")
    print("-" * 72)

    for p_key in sorted(patterns.keys()):
        total += 1
        p_data = patterns[p_key]

        size_n = _extract_size(p_key)
        if size_n is None:
            failed += 1; _fail(p_key, "---", "키에서 크기 추출 실패", fail_list); continue

        fset = filters.get(f"size_{size_n}")
        if not fset:
            failed += 1; _fail(p_key, "---", f"size_{size_n} 필터 없음", fail_list); continue

        filter_map = {kind: fset.get(kind) for kind in PATTERN_KINDS}
        if any(v is None for v in filter_map.values()):
            failed += 1; _fail(p_key, "---", "cross 또는 x 필터 누락", fail_list); continue

        inp = p_data.get("input")
        raw_exp = p_data.get("expected")
        if inp is None or raw_exp is None:
            failed += 1; _fail(p_key, str(raw_exp or "---"), "input/expected 필드 없음", fail_list); continue

        expected = normalize_label(raw_exp)
        if expected is None:
            failed += 1; _fail(p_key, str(raw_exp), f"라벨 정규화 실패: '{raw_exp}'", fail_list); continue

        # 크기 검증: 입력 패턴 + 모든 필터
        targets = [(inp, "입력 패턴")] + [(filter_map[k], f"{k} 필터") for k in PATTERN_KINDS]
        err = next(
            ((lbl, msg) for mat, lbl in targets for ok, msg in [validate_matrix(mat, size_n)] if not ok),
            None
        )
        if err:
            failed += 1; _fail(p_key, expected, f"{err[0]} 크기 오류: {err[1]}", fail_list); continue

        score_cross, t_cross = measure(inp, filter_map["cross"])
        score_x,     t_x     = measure(inp, filter_map["x"])
        perf.setdefault(size_n, []).append((t_cross + t_x) / 2)

        judgment = judge(score_cross, score_x)
        if judgment == expected:
            result_str = "PASS"; passed += 1
        else:
            result_str = "FAIL"; failed += 1
            reason = (f"UNDECIDED (expected: {expected})" if judgment == "UNDECIDED"
                      else f"{judgment} != {expected}")
            fail_list.append((p_key, reason))

        print(f"  {p_key:<16} {score_cross:<11.2f} {score_x:<11.2f} {judgment:<11} {expected:<10} {result_str}")

    # 성능 표: 3×3 기준 + data.json 수집 크기
    base3 = generate_pattern(3, "cross")
    _, t3 = measure(base3, base3)
    perf_results = [(3, t3)] + [(n, sum(ts) / len(ts)) for n, ts in sorted(perf.items())]
    print_performance_table(perf_results)

    # 결과 리포트
    print("\n" + "=" * 65)
    print(" 결과 리포트")
    print("=" * 65)
    print(f"  전체 테스트 수 : {total}")
    print(f"  통과 (PASS)    : {passed}")
    print(f"  실패 (FAIL)    : {failed}")
    if fail_list:
        print("\n  --- 실패 케이스 ---")
        for key, reason in fail_list:
            print(f"  {key}: {reason}")
    else:
        print("\n  모든 테스트 통과!")
        print("  → 라벨 정규화(+→Cross, x→X)와 epsilon 비교 정책으로 0 FAIL 달성.")
    print("=" * 65)


# 메인

def main():
    print_banner()
    menu = {
        "1": ("사용자 입력 (3x3 직접 입력)",  mode_1_user_input),
        "2": ("data.json 분석 (일괄 판정)",    mode_2_json_analysis),
        "3": ("data.json 생성만",              lambda: build_data_json("data.json")),
    }
    try:
        while True:
            print("실행 모드를 선택하세요:")
            for k, (desc, _) in menu.items():
                print(f"  {k}) {desc}")
            print("  q) 종료\n")

            choice = input("선택 >>> ").strip()
            if choice in menu:
                menu[choice][1]()
            elif choice.lower() == "q":
                print("\n프로그램을 종료합니다. 수고하셨습니다!")
                break
            else:
                print("잘못된 입력입니다. 1, 2, 3, q 중 선택하세요.")
            print()
    except (KeyboardInterrupt, EOFError):
        print("\n\n프로그램을 종료합니다. 수고하셨습니다!")


if __name__ == "__main__":
    main()
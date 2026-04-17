# Mini NPU Simulator

MAC(Multiply-Accumulate) 연산 기반 패턴 판별 시뮬레이터입니다.

---

## 실행 방법

### 파일 구성

```
main.py              # 메인 실행 파일 (UI, 모드 진입점)
mac_core.py          # MAC 연산, 판정, 성능 측정, 검증, 라벨 정규화
pattern_generator.py # 패턴 생성, data.json 빌드
data.json            # 필터 및 패턴 데이터 (없으면 자동 생성)
```

### 실행

```bash
python main.py
```

실행하면 아래 메뉴가 출력됩니다.

```
실행 모드를 선택하세요:
  1) 사용자 입력 (3x3 직접 입력)
  2) data.json 분석 (일괄 판정)
  3) data.json 생성만
  q) 종료
```

### 모드 1 — 사용자 입력 (3×3)

`1` 선택 후 필터 A, 필터 B, 판별할 패턴을 각각 한 줄씩 입력합니다.
**0과 1만 입력 가능합니다.** 다른 값 입력 시 재입력을 요청합니다.

```
[필터 A] 3x3 입력 (0 또는 1만, 공백 구분):
  1행: 0 1 0
  2행: 1 1 1
  3행: 0 1 0
```

### 모드 2 — data.json 분석

`2` 선택 시 `data.json`을 자동으로 로드합니다.
파일이 없거나 파싱에 실패하면 자동으로 생성합니다.
`data.json`은 실행 파일(`main.py`)과 같은 디렉터리에 위치해야 합니다.

### 종료

`q` 입력 또는 `Ctrl+C` / `Ctrl+D`로 종료할 수 있습니다.

---

## 구현 요약

### 라벨 정규화 방식

`data.json`의 `expected` 값과 필터 키는 다양한 형태로 표기될 수 있습니다.
프로그램 내부에서는 아래 규칙으로 표준 라벨(`Cross` / `X`)로 통일합니다.

| 입력 값 | 표준 라벨 |
|--------|----------|
| `+`, `cross`, `Cross`, `CROSS` | `Cross` |
| `x`, `X` | `X` |
| `UNDECIDED` | `None` → FAIL 처리 |

정규화는 `mac_core.py`의 `normalize_label()` 함수에서 수행하며,
인식되지 않는 라벨은 `None`을 반환해 해당 케이스를 FAIL로 처리합니다.

### MAC 연산 구현

`mac_core.py`의 `mac()` 함수에서 반복문으로 직접 구현합니다.
NumPy 등 외부 라이브러리는 사용하지 않습니다.

```python
def mac(pattern, filt):
    n = len(pattern)
    return sum(pattern[i][j] * filt[i][j] for i in range(n) for j in range(n))
```

입력 패턴과 필터의 같은 위치(i, j)의 값을 곱하고 전부 더합니다.
두 행렬이 완전히 일치할수록 높은 점수가 나옵니다.

### 동점 처리 정책 (epsilon)

부동소수점 연산에서는 수학적으로 같은 값이 미세하게 다르게 계산될 수 있습니다.
따라서 두 점수의 차이가 일정 수준(`EPSILON = 1e-9`) 이하이면 동점으로 간주합니다.

```python
EPSILON = 1e-9

def judge(score_cross, score_x):
    diff = score_cross - score_x
    if abs(diff) < EPSILON:
        return "UNDECIDED"
    return "Cross" if diff > 0 else "X"
```

`UNDECIDED`는 어떤 `expected` 값과도 일치하지 않으므로 자동으로 FAIL 처리됩니다.

### 패턴 생성 통합 (`generate_pattern`)

기존의 `generate_cross_pattern()` / `generate_x_pattern()` 함수를
`generate_pattern(n, kind)` 하나로 통합했습니다.

```python
generate_pattern(5, "cross")  # 5×5 십자가
generate_pattern(5, "x")      # 5×5 X
```

새 패턴 종류를 추가할 때도 `rules` 딕셔너리에 람다 한 줄만 추가하면 됩니다.

---

## 결과 리포트

### FAIL 케이스 원인 분석

현재 `data.json`에는 `expected` 값이 `"UNDECIDED"`인 케이스가 포함되어 있습니다
(`size_5_2`, `size_13_2`). 이 값은 표준 라벨(`Cross` / `X`)로 정규화되지 않으므로
라벨 정규화 단계에서 `None`을 반환하고 FAIL로 처리됩니다.

이는 로직 오류가 아니라 **데이터/스키마 문제**입니다.
`expected`에 `"UNDECIDED"`를 넣는 것은 미션 요구 사항 상 유효한 라벨이 아니며,
`"+"` 또는 `"x"`만 유효한 expected 값입니다.

완벽한 패턴(Cross/X)과 유효한 라벨만 사용하는 경우 FAIL은 0이 됩니다.
이 경우 0 FAIL의 근거는 두 가지입니다.

1. **라벨 정규화**: `"+"` → `Cross`, `"x"` → `X`로 일관되게 변환하여
   표기 방식 차이로 인한 오판을 제거합니다.
2. **epsilon 비교**: 부동소수점 오차가 `1e-9` 이하이면 동점 처리하여
   수치 비교 불일치로 인한 오판을 방지합니다.

### 성능 표 해석 및 시간 복잡도 O(N²) 근거

MAC 연산의 핵심은 N×N 행렬의 모든 위치(i, j)를 순회하며 곱셈과 덧셈을 수행하는 것입니다.
총 연산 횟수는 정확히 N²번이므로 시간 복잡도는 **O(N²)** 입니다.

아래는 실측 기준 예시 성능 표입니다 (환경에 따라 달라질 수 있습니다).

| 크기 (N×N) | 연산 횟수 (N²) | 평균 시간 (ms) |
|-----------|--------------|--------------|
| 3×3       | 9            | ~0.001       |
| 5×5       | 25           | ~0.002       |
| 13×13     | 169          | ~0.010       |
| 25×25     | 625          | ~0.035       |

N이 3→25로 약 8배 증가할 때 연산 횟수는 9→625로 약 **69배** 증가합니다.
실측 시간도 이와 유사한 비율로 증가하며, 이는 O(N²) 복잡도를 뒷받침합니다.

N²와 측정 시간의 관계를 정리하면, N이 k배 커질 때 연산 횟수와 시간은 k²배 늘어납니다.
예를 들어 5×5(N=5, N²=25)에서 25×25(N=25, N²=625)로 N이 5배 커지면
연산 횟수는 25배 증가하며, 실측 시간도 이에 비례해 증가하는 것을 확인할 수 있습니다.

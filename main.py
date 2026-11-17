import json
import time

EPSILON = 1e-9   # 0.000000001 보다 차이가 작으면 같다고 봄


# ── 1계단: MAC 연산 ──
def mac(pattern, filt):
    total = 0
    n = len(pattern)
    for i in range(n):
        for j in range(n):
            total += pattern[i][j] * filt[i][j]
    return total


# ── 2계단: 점수 비교 ──
def judge(score_a, score_b):
    if abs(score_a - score_b) < EPSILON:
        return "UNDECIDED"
    elif score_a > score_b:
        return "A"
    else:
        return "B"


# ── 3계단: 입력받기 ──
def read_matrix(name, n=3):
    print(f"\n[{name}] {n}줄을 입력하세요. (한 줄에 숫자 {n}개, 공백으로 구분)")
    matrix = []
    while len(matrix) < n:
        line = input(f"{len(matrix) + 1}번째 줄: ")
        parts = line.split()

        if len(parts) != n:
            print(f"입력 형식 오류: 각 줄에 {n}개의 숫자를 공백으로 구분해 입력하세요.")
            continue

        try:
            row = [float(p) for p in parts]
        except ValueError:
            print("입력 형식 오류: 숫자만 입력하세요.")
            continue

        matrix.append(row)
    return matrix


def print_matrix(matrix):
    for row in matrix:
        print("  " + " ".join(str(v) for v in row))


# ── 4계단: 시간 재기 ──
def measure_time(pattern, filt, repeat=10):
    total = 0
    for _ in range(repeat):
        start = time.perf_counter()
        mac(pattern, filt)
        end = time.perf_counter()
        total += (end - start)
    return total / repeat * 1000


def print_perf_table(rows):
    print("\n[성능 분석] (각 크기별 10회 평균)")
    print(f"{'크기':<10}{'평균 시간(ms)':<16}{'연산 횟수(N²)':<10}")
    print("-" * 38)
    for n, avg_ms in rows:
        print(f"{f'{n}×{n}':<10}{avg_ms:<16.6f}{n * n:<10}")


# ── 5계단: data.json 채점 ──

# 이름표 바꾸기 사전: 여러 모양의 이름표를 "Cross" 또는 "X" 하나로 통일
LABEL_MAP = {
    "+": "Cross",
    "cross": "Cross",
    "x": "X",
}


def normalize_label(raw):
    key = str(raw).strip().lower()      # 앞뒤 공백 제거 + 소문자로
    return LABEL_MAP.get(key)           # 사전에 없으면 None


def is_square(matrix, n):
    # n줄이고, 모든 줄이 n칸인지 검사
    if not isinstance(matrix, list) or len(matrix) != n:
        return False
    for row in matrix:
        if not isinstance(row, list) or len(row) != n:
            return False
    return True


def make_cross(n):
    m = n // 2
    return [[1 if (i == m or j == m) else 0 for j in range(n)] for i in range(n)]


def make_x(n):
    return [[1 if (i == j or i + j == n - 1) else 0 for j in range(n)] for i in range(n)]


def run_json_mode(path="data.json"):
    # 1) 파일 읽기
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ {path} 파일을 찾을 수 없습니다. main.py와 같은 폴더에 넣어주세요.")
        return
    except json.JSONDecodeError as e:
        print(f"❌ {path} 형식이 올바른 JSON이 아닙니다: {e}")
        return

    # 2) 필터 로드 + 이름표 정규화  →  filters[5] = {"Cross": [...], "X": [...]}
    filters = {}
    print("\n[필터 로드]")
    for size_key, pair in data.get("filters", {}).items():
        try:
            n = int(size_key.split("_")[1])          # "size_13" → 13
        except (IndexError, ValueError):
            print(f"  ⚠ 알 수 없는 필터 키: {size_key} (건너뜀)")
            continue
        filters[n] = {}
        for label_key, matrix in pair.items():
            label = normalize_label(label_key)
            if label is None:
                print(f"  ⚠ {size_key}의 알 수 없는 라벨: {label_key} (건너뜀)")
                continue
            filters[n][label] = matrix
        print(f"  ✅ {n}×{n} 필터 로드: {', '.join(filters[n].keys())}")

    # 3) 패턴 하나씩 채점
    print("\n[패턴 채점]")
    total = 0
    passed = 0
    failures = []    # (케이스 이름, 실패 이유)

    for case_id, case in data.get("patterns", {}).items():
        total += 1

        # 3-1) 키에서 N 꺼내기: "size_13_2" → 13
        try:
            n = int(case_id.split("_")[1])
        except (IndexError, ValueError):
            reason = "키 형식 오류 (size_N_번호 형태가 아님)"
            print(f"  {case_id}: FAIL - {reason}")
            failures.append((case_id, reason))
            continue

        # 3-2) 맞는 필터가 있나?
        if n not in filters or "Cross" not in filters[n] or "X" not in filters[n]:
            reason = f"size_{n} 필터(Cross/X)가 없음"
            print(f"  {case_id}: FAIL - {reason}")
            failures.append((case_id, reason))
            continue

        # 3-3) expected 정규화
        expected = normalize_label(case.get("expected"))
        if expected is None:
            reason = f"expected 라벨을 알 수 없음: {case.get('expected')}"
            print(f"  {case_id}: FAIL - {reason}")
            failures.append((case_id, reason))
            continue

        # 3-4) 크기 검사
        pattern = case.get("input")
        if not is_square(pattern, n):
            rows = len(pattern) if isinstance(pattern, list) else "?"
            reason = f"크기 불일치 (필터 {n}×{n}, 패턴 {rows}줄)"
            print(f"  {case_id}: FAIL - {reason}")
            failures.append((case_id, reason))
            continue

        # 3-5) MAC 계산 + 판정
        score_cross = mac(pattern, filters[n]["Cross"])
        score_x = mac(pattern, filters[n]["X"])
        result = judge(score_cross, score_x)
        verdict = {"A": "Cross", "B": "X", "UNDECIDED": "UNDECIDED"}[result]

        if verdict == expected:
            passed += 1
            mark = "PASS"
        else:
            mark = "FAIL"
            failures.append((case_id, f"판정 {verdict} ≠ 정답 {expected}"))

        print(f"  {case_id}: Cross={score_cross}, X={score_x} → 판정 {verdict} "
              f"/ 정답 {expected} → {mark}")

    # 4) 성능 분석 (3×3 포함)
    rows = []
    rows.append((3, measure_time(make_cross(3), make_x(3))))
    for n in sorted(filters):
        rows.append((n, measure_time(make_cross(n), filters[n]["Cross"])))
    print_perf_table(rows)

    # 5) 결과 요약
    print("\n[결과 요약]")
    print(f"  전체 테스트: {total}개")
    print(f"  통과: {passed}개")
    print(f"  실패: {len(failures)}개")
    if failures:
        print("  실패 케이스:")
        for case_id, reason in failures:
            print(f"    - {case_id}: {reason}")


# ── 모드 1: 사용자 입력 ──
def run_input_mode():
    filter_a = read_matrix("필터 A")
    filter_b = read_matrix("필터 B")

    print("\n✅ 필터 저장 완료")
    print("필터 A:")
    print_matrix(filter_a)
    print("필터 B:")
    print_matrix(filter_b)

    pattern = read_matrix("패턴")

    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)
    print(f"\nA 점수: {score_a} / B 점수: {score_b} / 판정: {judge(score_a, score_b)}")

    avg_ms = measure_time(pattern, filter_a)
    print_perf_table([(3, avg_ms)])


# ── 실행: 모드 선택 ──
def main():
    print("=== Mini NPU 시뮬레이터 ===")
    print("1. 사용자 입력 (3×3)")
    print("2. data.json 분석")
    while True:
        choice = input("선택 (1 또는 2): ").strip()
        if choice == "1":
            run_input_mode()
            break
        elif choice == "2":
            run_json_mode()
            break
        else:
            print("1 또는 2만 입력하세요.")


if __name__ == "__main__":
    main()

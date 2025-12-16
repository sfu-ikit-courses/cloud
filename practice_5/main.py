from concurrent.futures import ThreadPoolExecutor
import os

DIVS = tuple(range(2, 10))


def count_divisors(x: int) -> int:
    c = 0
    for d in DIVS:
        if x % d == 0:
            c += 1
    return c


def process_chunk(arr, result, start, end):
    # Обрабатываем индексы [start, end)
    for i in range(start, end):
        result[i] = count_divisors(arr[i])


def parallel_count(arr, max_workers=None):
    n = len(arr)
    result = [0] * n
    if n == 0:
        return result

    # Разумное число потоков
    if max_workers is None:
        max_workers = min(n, (os.cpu_count() or 1))

    workers = max(1, min(max_workers, n))
    chunk = (n + workers - 1) // workers

    ranges = []
    for w in range(workers):
        start = w * chunk
        end = min(start + chunk, n)
        if start < end:
            ranges.append((start, end))

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(process_chunk, arr, result, s, e) for s, e in ranges]
        for f in futures:
            f.result()

    return result


def main():
    # Ввод:
    # n
    # a1 a2 ... an
    import sys

    data = sys.stdin.read().strip().split()
    if not data:
        return
    n = int(data[0])
    arr = list(map(int, data[1:n + 1]))

    res = parallel_count(arr)
    print(*res)


if __name__ == "__main__":
    main()

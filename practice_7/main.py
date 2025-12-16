from concurrent.futures import ThreadPoolExecutor
import os
import threading
from collections import deque

DIVS = tuple(range(2, 10))


def count_divisors(x: int) -> int:
    c = 0
    for d in DIVS:
        if x % d == 0:
            c += 1
    return c


def process_chunk(arr, result, start, end, shared_q, q_sem, worker_no: int, limit_sem):
    # Ограничиваем количество одновременно работающих потоков до L
    with limit_sem:
        thread_id = threading.get_ident()
        for i in range(start, end):
            x = arr[i]
            cnt = count_divisors(x)
            result[i] = cnt

            # Критическая секция (через семафор)
            with q_sem:
                shared_q.append((worker_no, thread_id, i, x, cnt))


def parallel_count(arr, L: int, max_workers=None):
    n = len(arr)
    result = [0] * n
    if n == 0:
        return result, deque()

    if max_workers is None:
        max_workers = min(n, (os.cpu_count() or 1))

    # Общая очередь + "мьютекс" на семафоре (двоичный семафор)
    shared_q = deque()
    q_sem = threading.BoundedSemaphore(1)

    workers = max(1, min(max_workers, n))
    chunk = (n + workers - 1) // workers

    # Ограничитель параллелизма до L
    L = min(max(1, int(L)), workers)
    limit_sem = threading.Semaphore(L)

    ranges = []
    for w in range(workers):
        start = w * chunk
        end = min(start + chunk, n)
        if start < end:
            ranges.append((start, end))

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = []
        for worker_no, (s, e) in enumerate(ranges, start=1):
            futures.append(
                ex.submit(
                    process_chunk,
                    arr,
                    result,
                    s,
                    e,
                    shared_q,
                    q_sem,
                    worker_no,
                    limit_sem,
                )
            )
        for f in futures:
            f.result()

    return result, shared_q


def main():
    import sys

    data = sys.stdin.read().strip().split()
    if not data:
        return

    # Формат ввода:
    # n L
    # a1 a2 ... an
    n = int(data[0])
    L = int(data[1])
    arr = list(map(int, data[2:n + 2]))

    res, q = parallel_count(arr, L=L)

    print(*res)

    print(
        f"{'Worker':<8} {'ThreadID':<15} {'Index':<6} {'Value':<8} {f'Divs[{DIVS[0]}..{DIVS[-1]}]':<10}"
    )
    print("-" * 55)
    for worker_no, thread_id, idx, x, cnt in q:
        print(f"{worker_no:<8} {thread_id:<15} {idx:<6} {x:<8} {cnt:<10}")


if __name__ == "__main__":
    main()

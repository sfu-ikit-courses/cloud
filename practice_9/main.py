from concurrent.futures import ThreadPoolExecutor
import threading
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Circle:
    x: float
    y: float
    r: float


def disks_intersect(a: Circle, b: Circle) -> bool:
    dx = a.x - b.x
    dy = a.y - b.y
    return (dx * dx + dy * dy) <= (a.r + b.r) ** 2


def generate_circles(
    n: int, rng: random.Random, xy_min: float, xy_max: float, r_min: float, r_max: float
) -> list[Circle]:
    res = []
    for _ in range(n):
        x = rng.uniform(xy_min, xy_max)
        y = rng.uniform(xy_min, xy_max)
        r = rng.uniform(r_min, r_max)
        res.append(Circle(x, y, r))
    return res


def save_to_file(path: str, circles_a: list[Circle], circles_b: list[Circle]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("i,ax,ay,ar,bx,by,br\n")
        for i, (a, b) in enumerate(zip(circles_a, circles_b)):
            f.write(
                f"{i},{a.x:.6f},{a.y:.6f},{a.r:.6f},{b.x:.6f},{b.y:.6f},{b.r:.6f}\n"
            )


def run(
    n: int,
    out_path: str = "circles.csv",
    seed: int | None = None,
    xy_min: float = -10.0,
    xy_max: float = 10.0,
    r_min: float = 3.0,
    r_max: float = 8.0,
    max_attempts: int | None = None,
):
    # Shared state
    circles_a: list[Circle] = []
    circles_b: list[Circle] = []
    done = threading.Event()
    attempts = 0
    attempts_lock = threading.Lock()
    success = False

    def barrier_action():
        nonlocal attempts, success
        ok = True
        for i in range(n):
            if not disks_intersect(circles_a[i], circles_b[i]):
                ok = False
                break

        with attempts_lock:
            attempts += 1
            cur = attempts

        if ok:
            save_to_file(out_path, circles_a, circles_b)
            success = True
            done.set()
        else:
            if max_attempts is not None and cur >= max_attempts:
                success = False
                done.set()

    barrier = threading.Barrier(2, action=barrier_action)

    def worker(slot: str, seed_add: int):
        nonlocal circles_a, circles_b
        rng = random.Random(None if seed is None else (seed * 1_000_003 + seed_add))

        while not done.is_set():
            generated = generate_circles(n, rng, xy_min, xy_max, r_min, r_max)

            # Каждый поток пишет в свой слот — пересечений нет
            if slot == "A":
                circles_a = generated
            else:
                circles_b = generated

            # Точка синхронизации
            try:
                barrier.wait()
            except threading.BrokenBarrierError:
                return

    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(worker, "A", 1)
        f2 = ex.submit(worker, "B", 2)

        f1.result()
        f2.result()

    if not success and max_attempts is not None and attempts >= max_attempts:
        print(f"Остановлено по лимиту попыток: {attempts}.")
    else:
        print(f"Готово! Попыток: {attempts}. Файл: {out_path}")


def main():
    import sys

    data = sys.stdin.read().strip().split()
    if not data:
        print("Введите: N [seed] [max_attempts]")
        return

    # Формат ввода:
    # N [seed] [max_attempts]
    n = int(data[0])
    seed = int(data[1]) if len(data) >= 2 else None
    max_attempts = int(data[2]) if len(data) >= 3 else None

    run(n=n, seed=seed, max_attempts=max_attempts)


if __name__ == "__main__":
    main()

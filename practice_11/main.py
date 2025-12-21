from dataclasses import dataclass
from mpi4py import MPI
import numpy as np
import random


@dataclass(frozen=True)
class Params:
    n: int
    seed: int | None
    max_attempts: int | None
    out_path: str = "circles.csv"
    xy_min: float = -10.0
    xy_max: float = 10.0
    r_min: float = 3.0
    r_max: float = 8.0


def get_params() -> Params | None:
    """
    Формат ввода:
      N [seed] [max_attempts] [out_path]
    """
    import sys

    data = sys.stdin.read().strip().split()
    if not data:
        return None

    n = int(data[0])
    seed = int(data[1]) if len(data) >= 2 else None
    max_attempts = int(data[2]) if len(data) >= 3 else None
    out_path = data[3] if len(data) >= 4 else "circles.csv"

    return Params(n=n, seed=seed, max_attempts=max_attempts, out_path=out_path)


def broadcast_params(comm: MPI.Comm, params: Params | None) -> Params | None:
    """
    Рассылает параметры ввода всем процессам.
    """
    return comm.bcast(params, root=0)


def disks_intersect_xyrr(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    a, b: массивы формы (k, 3) float64, где столбцы: x, y, r
    Возвращает булев массив длины k: пересекаются ли диски.
    """
    dx = a[:, 0] - b[:, 0]
    dy = a[:, 1] - b[:, 1]
    rs = a[:, 2] + b[:, 2]
    return (dx * dx + dy * dy) <= (rs * rs)


def generate_circles(
    n: int,
    rng: random.Random,
    xy_min: float,
    xy_max: float,
    r_min: float,
    r_max: float,
) -> np.ndarray:
    """
    Генерирует N кругов как numpy массив (n, 3): x, y, r (float64).
    """
    out = np.empty((n, 3), dtype=np.float64)
    for i in range(n):
        out[i, 0] = rng.uniform(xy_min, xy_max)
        out[i, 1] = rng.uniform(xy_min, xy_max)
        out[i, 2] = rng.uniform(r_min, r_max)
    return out


def save_to_file(path: str, a: np.ndarray, b: np.ndarray) -> None:
    """
    a, b: (n, 3) float64
    """
    n = a.shape[0]
    with open(path, "w", encoding="utf-8") as f:
        f.write("i,ax,ay,ar,bx,by,br\n")
        for i in range(n):
            f.write(
                f"{i},"
                f"{a[i, 0]:.6f},{a[i, 1]:.6f},{a[i, 2]:.6f},"
                f"{b[i, 0]:.6f},{b[i, 1]:.6f},{b[i, 2]:.6f}\n"
            )


def split_range(n: int, size: int, rank: int) -> tuple[int, int]:
    """
    Делит индексы [0..n) равномерно по rank'ам.
    Возвращает (start, end) для данного rank.
    """
    base, rem = divmod(n, size)
    start = rank * base + min(rank, rem)
    end = start + base + (1 if rank < rem else 0)
    return start, end


def run(params: Params) -> None:
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    if size < 2:
        if rank == 0:
            print(
                "Нужно минимум 2 MPI-процесса: rank 0 генерирует A, rank 1 генерирует B."
            )
        return

    if params.seed is None:
        rng_a = random.Random()
        rng_b = random.Random()
    else:
        rng_a = random.Random(params.seed * 1_000_003 + 1)
        rng_b = random.Random(params.seed * 1_000_003 + 2)

    n = params.n

    circles_a = np.empty((n, 3), dtype=np.float64)
    circles_b = np.empty((n, 3), dtype=np.float64)

    start, end = split_range(n, size, rank)

    attempts = 0
    success = False

    while True:
        # rank 0 решает, продолжать ли ещё одну попытку
        if rank == 0:
            if params.max_attempts is not None and attempts >= params.max_attempts:
                go = False
            else:
                go = True
        else:
            go = None

        go = comm.bcast(go, root=0)
        if not go:
            break

        attempts += 1

        # Генерация: только rank 0 и rank 1
        if rank == 0:
            circles_a[:] = generate_circles(
                n, rng_a, params.xy_min, params.xy_max, params.r_min, params.r_max
            )
        if rank == 1:
            circles_b[:] = generate_circles(
                n, rng_b, params.xy_min, params.xy_max, params.r_min, params.r_max
            )

        # Разослать A и B всем
        comm.Bcast([circles_a, MPI.DOUBLE], root=0)
        comm.Bcast([circles_b, MPI.DOUBLE], root=1)

        # Локальная проверка для своего диапазона i
        if start < end:
            ok_slice = disks_intersect_xyrr(
                circles_a[start:end], circles_b[start:end]
            ).all()
        else:
            ok_slice = True  # пустой диапазон — "истина"

        # Глобальная проверка: все i должны быть True
        global_ok = comm.allreduce(ok_slice, op=MPI.LAND)

        if global_ok:
            success = True
            if rank == 0:
                save_to_file(params.out_path, circles_a, circles_b)
            break

    if rank == 0:
        if success:
            print(f"Готово! Попыток: {attempts}. Файл: {params.out_path}")
        else:
            if params.max_attempts is None:
                print(f"Остановлено. Попыток: {attempts}. (success=False)")
            else:
                print(f"Остановлено по лимиту попыток: {attempts}.")


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    params = get_params() if rank == 0 else None

    params = broadcast_params(comm, params)

    if params is None:
        if rank == 0:
            print("Введите: N [seed] [max_attempts] [out_path]")
        return

    run(params)


if __name__ == "__main__":
    main()

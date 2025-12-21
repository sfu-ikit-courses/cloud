from mpi4py import MPI
import numpy as np

DIVS = tuple(range(2, 10))


def count_divisors(a: np.ndarray) -> np.ndarray:
    res = np.zeros_like(a, dtype=np.int32)
    for d in DIVS:
        res += a % d == 0
    return res


def split_counts_displs(n: int, p: int):
    # Равномерно распределяем n элементов на p процессов
    base, rem = divmod(n, p)
    counts = np.array([base + (1 if i < rem else 0) for i in range(p)], dtype=np.int32)
    displs = np.zeros(p, dtype=np.int32)
    displs[1:] = np.cumsum(counts[:-1])
    return counts, displs


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # rank 0 читает вход
    if rank == 0:
        import sys

        data = sys.stdin.read().strip().split()
        if not data:
            n = 0
            arr = np.array([], dtype=np.int64)
        else:
            n = int(data[0])
            arr = np.array(list(map(int, data[1:n + 1])), dtype=np.int64)
    else:
        n = None
        arr = None

    # Рассылаем n всем
    n = comm.bcast(n, root=0)

    # Готовим counts/displs на root и рассылаем всем (чтобы каждый знал размер приёма)
    if rank == 0:
        counts, displs = split_counts_displs(n, size)
    else:
        counts = None
        displs = None

    counts = comm.bcast(counts, root=0)
    displs = comm.bcast(displs, root=0)

    # Scatterv: раздать куски массива
    local_n = int(counts[rank])
    local_arr = np.empty(local_n, dtype=np.int64)

    if n == 0:
        local_arr = np.array([], dtype=np.int64)
    else:
        comm.Scatterv(
            (
                [arr, counts, displs, MPI.INT64_T]
                if rank == 0
                else [None, counts, displs, MPI.INT64_T]
            ),
            local_arr,
            root=0,
        )

    local_res = count_divisors(local_arr)

    # Gatherv: собрать результаты на root
    if rank == 0:
        res = np.empty(n, dtype=np.int32)
    else:
        res = None

    if n != 0:
        comm.Gatherv(
            local_res, [res, counts, displs, MPI.INT] if rank == 0 else None, root=0
        )

    if rank == 0:
        if n == 0:
            print()
        else:
            print(*res.tolist())


if __name__ == "__main__":
    main()

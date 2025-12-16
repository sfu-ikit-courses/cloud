from concurrent.futures import ThreadPoolExecutor
import threading
import random
import os

POINTS = (10, 20, 30, 50, 90, 100)


class Competition:
    def __init__(self, n: int, m: int, seed: int | None = None):
        self.n = n
        self.m = m
        self.seed = seed

        # Shared state
        self.cond = threading.Condition()
        self.active = set(range(n))  # кто участвует в текущем туре
        self.targets = [i % m for i in range(n)]  # "мишень" стрелка

        self.scores = [0] * n  # очки в текущем туре
        self.round_done = [-1] * n
        self.finished_count = 0
        self.round_no = 0
        self.phase = "WAIT"  # WAIT -> SHOOT -> DONE
        self.winner = None

        self.rngs = []
        for archer_id in range(n):
            if seed is None:
                self.rngs.append(random.Random())
            else:
                self.rngs.append(random.Random(seed * 1_000_003 + archer_id))

        self.target_sem = threading.Semaphore(max(1, m))

    def shoot_three(self, archer_id: int) -> int:
        rng = self.rngs[archer_id]

        # 3 выстрела: суммируем случайные очки
        return sum(rng.choice(POINTS) for _ in range(3))

    def shoot_task(self, archer_id: int, round_no: int):
        with self.target_sem:
            points = self.shoot_three(archer_id)

        with self.cond:
            # тур сменился / стрелок выбыл / уже стрелял в этом туре
            if (
                self.phase != "SHOOT"
                or self.round_no != round_no
                or archer_id not in self.active
                or self.round_done[archer_id] == round_no
            ):
                return

            self.scores[archer_id] = points
            self.round_done[archer_id] = round_no
            self.finished_count += 1
            self.cond.notify_all()

    def run(self, max_workers: int | None = None):
        if max_workers is None:
            cpu = os.cpu_count() or 1
            max_workers = min(self.n, max(cpu, self.m * 2))

        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            while True:
                with self.cond:
                    self.round_no += 1
                    self.finished_count = 0
                    self.phase = "SHOOT"
                    round_no = self.round_no

                    active_list = sorted(self.active)
                    print(f"\n=== Старт тура {round_no}. Участники: {active_list} ===")

                    for archer_id in active_list:
                        ex.submit(self.shoot_task, archer_id, round_no)

                    # Ждём, пока все активные отстреляются
                    while self.finished_count < len(self.active):
                        self.cond.wait()

                    for i in active_list:
                        print(
                            f"Тур {round_no}: стрелок {i} (мишень {self.targets[i]}) набрал {self.scores[i]}"
                        )

                    # Все отстрелялись — выбираем максимум
                    best = max(self.scores[i] for i in self.active)
                    leaders = [i for i in self.active if self.scores[i] == best]

                    print(
                        f"Тур {round_no} завершён. Лучший результат: {best}. Лидеры: {leaders}"
                    )

                    if len(leaders) == 1:
                        self.winner = leaders[0]
                        self.phase = "DONE"
                        print(
                            f"\n🏆 Победитель: стрелок {self.winner}. Соревнование завершено."
                        )
                        break

                    self.active = set(leaders)


def main():
    import sys

    data = sys.stdin.read().strip().split()
    if not data:
        print("Введите: N M [seed]")
        return

    N = int(data[0])
    M = int(data[1])
    seed = int(data[2]) if len(data) > 2 else None

    Competition(N, M, seed=seed).run()


if __name__ == "__main__":
    main()

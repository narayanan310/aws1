"""Run each worker once; useful for local tests and demos."""

from app.workers.image_worker import ImageWorker


def main() -> None:
    for worker_cls in (ImageWorker,):
        worker_cls(once=True).run()


if __name__ == "__main__":
    main()


"""Run each worker once; useful for local tests and demos."""

from app.workers.ai_worker import AIWorker
from app.workers.embedding_worker import EmbeddingWorker
from app.workers.image_worker import ImageWorker


def main() -> None:
    for worker_cls in (ImageWorker, AIWorker, EmbeddingWorker):
        worker_cls(once=True).run()


if __name__ == "__main__":
    main()


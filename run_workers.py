"""Run all background workers continuously."""
#run_workers.py
import threading
import time

from app.workers.image_worker import ImageWorker


def start_worker(worker_cls) -> None:
    print(f"Starting {worker_cls.__name__} thread...")
    worker = worker_cls(once=False, sleep_seconds=1.0)
    worker.run()


def main() -> None:
    workers = [ImageWorker]
    threads = []
    
    for cls in workers:
        t = threading.Thread(target=start_worker, args=(cls,), daemon=True)
        t.start()
        threads.append(t)
        
    print("All workers started. Press Ctrl+C to exit.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down workers...")

if __name__ == "__main__":
    main()

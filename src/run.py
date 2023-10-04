# python src/run.py main:app --host 0.0.0.0 --port 8000 --reload
import uvicorn
from celery.contrib.testing.worker import start_worker
from celery_tasks import celery
original_callback = uvicorn.main.callback

def callback(**kwargs):
    with start_worker(celery, perform_ping_check=False, loglevel="info"):
        original_callback(**kwargs)
uvicorn.main.callback = callback


if __name__ == "__main__":
    uvicorn.main()

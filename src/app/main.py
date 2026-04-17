import asyncio
import logging

from app.tasks import run_rustore_tasks

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)

if __name__ == '__main__':
    asyncio.run(run_rustore_tasks())

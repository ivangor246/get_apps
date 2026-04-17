import asyncio

from app.tasks import run_rustore_tasks


if __name__ == '__main__':
    asyncio.run(run_rustore_tasks())

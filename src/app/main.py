import argparse
import asyncio
import logging

from app.tasks import run_index_task, run_rustore_app_info_tasks, run_rustore_tasks, run_serve_task

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)


def _build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI with 'categories' and 'apps' subcommands."""
    parser = argparse.ArgumentParser(prog='get_apps', description='RuStore data collector.')
    sub = parser.add_subparsers(dest='mode', required=True)

    categories_parser = sub.add_parser(
        'categories', help='Collect app IDs per category into saved_data/categories/<timestamp>/.'
    )
    categories_parser.add_argument(
        '--concurrency', type=int, default=3, help='Parallel page fetches (default: 3).'
    )

    apps_parser = sub.add_parser('apps', help='Collect detailed info about apps into a SQLite database.')
    apps_parser.add_argument('--db', required=True, help='SQLite database name (stored under saved_data/databases/).')
    apps_parser.add_argument(
        '--folder',
        default=None,
        help='Timestamp folder under saved_data/categories/ (default: latest).',
    )
    apps_parser.add_argument('--concurrency', type=int, default=3, help='Parallel page fetches (default: 3).')

    index_parser = sub.add_parser('index', help='Embed app_info rows into the Chroma collection.')
    index_parser.add_argument('--db', required=True, help='SQLite database name (stored under saved_data/databases/).')
    index_parser.add_argument('--batch-size', type=int, default=32, help='Embedding batch size (default: 32).')
    index_parser.add_argument(
        '--concurrency', type=int, default=1, help='Parallel embedding batches in flight (default: 1).'
    )

    serve_parser = sub.add_parser('serve', help='Run the RAG FastAPI backend.')
    serve_parser.add_argument('--db', required=True, help='SQLite database name (stored under saved_data/databases/).')
    serve_parser.add_argument('--host', default=None, help='Bind host (default: API_HOST from config).')
    serve_parser.add_argument('--port', type=int, default=None, help='Bind port (default: API_PORT from config).')

    return parser


async def _dispatch(args: argparse.Namespace) -> None:
    """Route parsed CLI args to the matching task coroutine."""
    if args.mode == 'categories':
        await run_rustore_tasks(concurrency=args.concurrency)
    elif args.mode == 'apps':
        await run_rustore_app_info_tasks(db_name=args.db, folder_name=args.folder, concurrency=args.concurrency)
    elif args.mode == 'index':
        await run_index_task(db_name=args.db, batch_size=args.batch_size, concurrency=args.concurrency)
    elif args.mode == 'serve':
        await run_serve_task(db_name=args.db, host=args.host, port=args.port)


if __name__ == '__main__':
    parsed = _build_parser().parse_args()
    try:
        asyncio.run(_dispatch(parsed))
    except KeyboardInterrupt:
        logging.getLogger(__name__).warning('Interrupted by user.')

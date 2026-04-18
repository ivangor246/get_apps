import argparse
import asyncio
import logging

from app.tasks import run_rustore_app_info_tasks, run_rustore_tasks

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)


def _build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI with 'categories' and 'apps' subcommands."""
    parser = argparse.ArgumentParser(prog='get_apps', description='RuStore data collector.')
    sub = parser.add_subparsers(dest='mode', required=True)

    sub.add_parser('categories', help='Collect app IDs per category into saved_data/categories/<timestamp>/.')

    apps_parser = sub.add_parser('apps', help='Collect detailed info about apps into a SQLite database.')
    apps_parser.add_argument('--db', required=True, help='SQLite database name (stored under saved_data/databases/).')
    apps_parser.add_argument(
        '--folder',
        default=None,
        help='Timestamp folder under saved_data/categories/ (default: latest).',
    )
    apps_parser.add_argument('--concurrency', type=int, default=3, help='Parallel page fetches (default: 3).')

    return parser


async def _dispatch(args: argparse.Namespace) -> None:
    """Route parsed CLI args to the matching task coroutine."""
    if args.mode == 'categories':
        await run_rustore_tasks()
    elif args.mode == 'apps':
        await run_rustore_app_info_tasks(db_name=args.db, folder_name=args.folder, concurrency=args.concurrency)


if __name__ == '__main__':
    parsed = _build_parser().parse_args()
    asyncio.run(_dispatch(parsed))

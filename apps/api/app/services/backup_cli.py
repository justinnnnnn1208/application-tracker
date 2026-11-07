import argparse
from pathlib import Path
from app.core.config import Settings
from app.services.backups import backup, restore


def main():
    parser = argparse.ArgumentParser(description="Private local backup/restore; restore only into a new folder.")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("--destination", type=Path, required=True)
    recover = commands.add_parser("restore")
    recover.add_argument("--archive", type=Path, required=True)
    recover.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "restore":
        restore(args.archive, args.destination)
        print("Restore verified in the new destination. Stop all services before switching databases.")
    else:
        backup(Settings.from_env(), args.destination)
        print("Backup created; checksum, database integrity and restoration checks passed.")


if __name__ == "__main__":
    main()

import fcntl
import os

from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import Task, now
from app.db.session import make_engine
from app.worker.tasks import catch_up, run_once


def main():
    os.umask(0o077)
    settings = Settings.from_env()
    engine = make_engine(settings.database_url)
    settings.storage_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = (settings.storage_dir / ".worker.lock").open("a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit("A worker is already running for this storage folder.")
    with Session(engine) as session:
        # An interrupted remote operation is for manual review, never an automatic replay.
        for task in session.scalars(select(Task).where(Task.status == "RUNNING")):
            task.status, task.message, task.finished_at = "NEEDS_INPUT", "Worker stopped during this task. Review the outcome before creating another task.", now()
        session.commit()
        catch_up(session)

    def tick():
        try:
            with Session(engine) as session:
                catch_up(session)
            run_once(engine, settings)
        except Exception:
            print("Worker tick failed; private error details were not logged.", flush=True)

    scheduler = BlockingScheduler(timezone="Europe/London")
    scheduler.add_job(tick, "interval", seconds=1, max_instances=1, coalesce=True)
    print("Local worker ready. Scheduled jobs run only while the app is open.", flush=True)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        engine.dispose()
        lock.close()


if __name__ == "__main__":
    main()

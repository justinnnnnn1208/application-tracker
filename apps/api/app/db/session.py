from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from fastapi import Request


def make_engine(url: str):
    engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
    return engine


def get_session(request: Request):
    with Session(request.app.state.engine) as session:
        yield session

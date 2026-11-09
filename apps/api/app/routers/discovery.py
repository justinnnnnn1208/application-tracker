from fastapi import APIRouter, HTTPException
from pydantic import field_validator
from sqlalchemy import select

from app.db.models import DiscoverySource
from app.integrations.discovery.greenhouse import validate_board
from app.routers.tracker import DB, require
from app.routers.workflows import TaskOut, enqueue
from app.schemas import StrictModel

router = APIRouter()


class SourceData(StrictModel):
    board: str
    enabled: bool = False

    @field_validator("board")
    @classmethod
    def slug(cls, value):
        return validate_board(value)


def source_out(source):
    return {"id": source.id, "provider": source.provider, "board": source.board, "enabled": source.enabled}


@router.get("/discovery")
def sources(session: DB):
    return [source_out(source) for source in session.scalars(select(DiscoverySource).order_by(DiscoverySource.id))]


@router.post("/discovery", status_code=201)
def add_source(data: SourceData, session: DB):
    if session.scalar(select(DiscoverySource).where(DiscoverySource.provider == "greenhouse", DiscoverySource.board == data.board)):
        raise HTTPException(409, "This board is already configured")
    source = DiscoverySource(provider="greenhouse", **data.model_dump())
    session.add(source)
    session.commit()
    return source_out(source)


@router.delete("/discovery/{id}", status_code=204)
def delete_source(id: str, session: DB):
    source = require(session, DiscoverySource, id)
    session.delete(source)
    session.commit()


class DiscoverData(StrictModel):
    source_id: str


@router.post("/tasks/discover", response_model=TaskOut, status_code=202)
def discover(data: DiscoverData, session: DB):
    source = require(session, DiscoverySource, data.source_id)
    if not source.enabled:
        raise HTTPException(409, "Enable the source before discovering jobs")
    return enqueue(session, "discover", {"source_id": source.id})

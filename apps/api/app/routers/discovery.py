from fastapi import APIRouter, HTTPException
from typing import Literal
from pydantic import Field, field_validator, model_validator
from sqlalchemy import select

from app.db.models import DiscoverySource
from app.integrations.discovery.greenhouse import validate_board
from app.integrations.discovery.reed import configured as reed_configured
from app.routers.tracker import DB, require
from app.routers.workflows import TaskOut, enqueue
from app.schemas import StrictModel

router = APIRouter()


class SourceData(StrictModel):
    board: str = ""
    search_query: str = Field(default="", max_length=300)
    provider: Literal["greenhouse", "lever", "ashby", "reed"] = "greenhouse"
    employer: str = Field(default="", max_length=200)
    region: Literal["global", "eu"] = "global"
    enabled: bool = False

    @field_validator("board")
    @classmethod
    def slug(cls, value):
        return validate_board(value) if value else value


    @model_validator(mode="after")
    def provider_settings(self):
        if self.provider == "reed":
            if not self.search_query.strip() or self.employer:
                raise ValueError("Reed needs keywords; employer comes from the API")
            self.board = "search"
        elif not self.board or self.search_query:
            raise ValueError("Boards require a slug, not search keywords")
        if self.provider in {"lever", "ashby"} and not self.employer.strip():
            raise ValueError("Supply the employer name shown on this board")
        if self.provider != "lever" and self.region != "global":
            raise ValueError("Region applies only to Lever")
        return self


def source_out(source):
    return {"id": source.id, "provider": source.provider, "board": source.board, "enabled": source.enabled, "employer": source.employer, "region": source.region, "search_query": source.search_query, "credentials_configured": source.provider != "reed" or reed_configured()}


@router.get("/discovery")
def sources(session: DB):
    return [source_out(source) for source in session.scalars(select(DiscoverySource).order_by(DiscoverySource.id))]


@router.post("/discovery", status_code=201)
def add_source(data: SourceData, session: DB):
    if session.scalar(select(DiscoverySource).where(DiscoverySource.provider == data.provider, DiscoverySource.board == data.board, DiscoverySource.region == data.region, DiscoverySource.search_query == data.search_query)):
        raise HTTPException(409, "This board is already configured")
    source = DiscoverySource(**data.model_dump())
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
    if source.provider == "reed" and not reed_configured():
        raise HTTPException(409, "Configure REED_API_KEY privately before importing Reed jobs.")
    if not source.enabled:
        raise HTTPException(409, "Enable the source before discovering jobs")
    return enqueue(session, "discover", {"source_id": source.id})

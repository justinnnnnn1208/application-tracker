from fastapi import APIRouter, HTTPException, Request

from app.db.models import Job, new_id
from app.routers.tracker import DB, require
from app.routers.workflows import TaskOut, enqueue
from app.services.sponsor_register import MAX_BYTES, RegisterImport, metadata, match

router = APIRouter()


@router.get('/sponsors/register')
def register_status(session: DB):
    return metadata(session)


@router.get('/jobs/{id}/sponsor-register')
def job_register(id: str, session: DB):
    job = require(session, Job, id)
    matched, organisation = match(session, job.company)
    return {'match': matched, 'organisation': organisation, 'register': metadata(session)}


@router.post('/sponsors/register', response_model=TaskOut, status_code=202)
async def upload_register(request: Request, session: DB):
    try:
        config = RegisterImport.model_validate_json(request.headers.get('X-Register-Metadata', ''))
    except ValueError:
        raise HTTPException(422, 'Supply official CSV source, publication date, column mapping and explicit confirmation.') from None
    folder = request.app.state.settings.storage_dir / 'registers'
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    file_id = new_id()
    path = folder / (file_id + '.csv')
    size = 0
    try:
        with path.open('xb') as file:
            path.chmod(0o600)
            async for chunk in request.stream():
                size += len(chunk)
                if size > MAX_BYTES:
                    raise HTTPException(413, 'Register CSV must be under 50 MB.')
                file.write(chunk)
        if not size:
            raise HTTPException(422, 'Choose a non-empty register CSV file.')
        return enqueue(session, 'import_sponsor_register', {'file_id': file_id, 'config': config.model_dump(mode='json')})
    except BaseException:
        path.unlink(missing_ok=True)
        raise

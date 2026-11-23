"""Public diagnostics must not open the tracker or turn transport into acceptance."""
import json
import sqlite3

import pytest
import sqlalchemy

from app.schemas import JobData
from app.services import discovery_check as diagnostic
from app.services.errors import NeedsInput


def vacancy():
    return JobData(url='https://example.org/public-vacancy',company='Fixture Company',title='Junior Engineer',location='London',description='Source text omitted from report',notes='synthetic-private-note-marker')


@pytest.mark.parametrize('provider',diagnostic.PROVIDERS)
def test_uses_existing_public_adapters_without_database_or_model(provider,monkeypatch):
    calls=[]
    def reader(*args):calls.append(args);return [vacancy()],2
    module=getattr(diagnostic,provider)
    monkeypatch.setattr(module,'read_search' if provider=='reed' else 'read_board',reader)
    monkeypatch.setattr(sqlalchemy,'create_engine',lambda *_args,**_kwargs:pytest.fail('No app engine'))
    monkeypatch.setattr(sqlite3,'connect',lambda *_args,**_kwargs:pytest.fail('No tracker DB'))
    args={'query':'graduate technology'} if provider=='reed' else {'board':'fixture','employer':'Fixture Company'}
    report=diagnostic.check(provider,**args)
    assert len(calls)==1 and report['state']=='COMPLETED'
    assert report['postings_read']==1 and report['skipped']==2 and report['descriptions_present']==1
    assert report['quality_assessed'] is False and report['phase_2_accepted'] is False
    assert 'synthetic-private-note-marker' not in json.dumps(report,default=str)
    assert 'Source text omitted from report' not in json.dumps(report,default=str)
    assert len(report['samples'][0]['description_sha256'])==64


def test_empty_board_is_not_a_passing_vacancy_check(monkeypatch):
    monkeypatch.setattr(diagnostic.greenhouse,'read_board',lambda _:([],0))
    report=diagnostic.check('greenhouse',board='fixture')
    assert report['state']=='NOT TESTED' and report['postings_read']==0
    assert report['phase_2_accepted'] is False


def test_denial_never_echoes_response_or_private_configuration(monkeypatch):
    def denied(*_):raise NeedsInput('synthetic-private-response-marker')
    monkeypatch.setattr(diagnostic.greenhouse,'read_board',denied)
    report=diagnostic.check('greenhouse',board='fixture')
    assert report['state']=='NOT TESTED' and 'synthetic-private' not in str(report)


@pytest.mark.parametrize('arguments',[
    {'provider':'unknown','board':'fixture'},
    {'provider':'lever','board':'fixture'},
    {'provider':'ashby','board':'fixture','employer':'Fixture','region':'eu'},
    {'provider':'greenhouse','board':'https://example.org'},
    {'provider':'greenhouse','board':'fixture','query':'keywords'},
    {'provider':'reed','query':'','board':'fixture'},
    {'provider':'reed','query':'graduate','employer':'Owner employer'},
])
def test_invalid_scope_stops_before_public_fetch(arguments,monkeypatch):
    for name in diagnostic.PROVIDERS:
        module=getattr(diagnostic,name)
        monkeypatch.setattr(module,'read_search' if name=='reed' else 'read_board',lambda *_args:pytest.fail('No fetch for invalid scope'))
    with pytest.raises(ValueError):diagnostic.check(**arguments)


def test_cli_writes_private_new_report_and_does_not_overwrite(tmp_path,monkeypatch,capsys):
    output=tmp_path/'reports/source.json'
    monkeypatch.setattr(diagnostic.greenhouse,'read_board',lambda _:([vacancy()],0))
    monkeypatch.setattr('sys.argv',['discovery_check','--provider','greenhouse','--board','fixture','--output',str(output)])
    assert diagnostic.main()==0
    original=output.read_bytes()
    assert output.stat().st_mode & 0o777 == 0o600
    assert json.loads(original)['phase_2_accepted'] is False
    assert diagnostic.main()==2 and output.read_bytes()==original
    assert 'synthetic-private-note-marker' not in capsys.readouterr().out


def test_cancelled_check_creates_no_fake_completed_report(tmp_path,monkeypatch,capsys):
    output=tmp_path/'cancelled.json'
    def cancelled(*_args,**_kwargs):raise KeyboardInterrupt
    monkeypatch.setattr(diagnostic,'check',cancelled)
    monkeypatch.setattr('sys.argv',['discovery_check','--provider','greenhouse','--board','fixture','--output',str(output)])
    assert diagnostic.main()==130 and not output.exists()
    assert 'cancelled' in capsys.readouterr().out

"""The Mac model-check shortcut reuses the public runner without app secrets."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT=Path(__file__).resolve().parents[3]


def launcher(tmp_path,monkeypatch,*,interpreter=True):
    spec=importlib.util.spec_from_file_location('tracker_dev_launcher',ROOT/'scripts/dev.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    monkeypatch.setattr(module,'ROOT',tmp_path)
    monkeypatch.setattr(module.sys,'argv',['scripts/dev.py','--check-model'])
    for key in ['LLM_PROVIDER','LLM_MODEL','LLM_BASE_URL']:
        monkeypatch.delenv(key,raising=False)
    if interpreter:
        python=tmp_path/'apps/api/.venv/bin/python';python.parent.mkdir(parents=True);python.touch()
    monkeypatch.setattr(module.subprocess,'Popen',lambda *_args,**_kwargs:pytest.fail('Do not start app services for public model evaluation'))
    return module


def test_model_check_loads_private_model_selectors_but_never_passes_secrets_or_db_settings(tmp_path,monkeypatch,capsys):
    module=launcher(tmp_path,monkeypatch)
    secret='synthetic-private-marker-not-a-real-key'
    (tmp_path/'.env').write_text(f'LLM_PROVIDER=ollama\nLLM_MODEL=private-config-model\nLLM_BASE_URL=http://127.0.0.1:11434/v1\nAPP_ACCESS_TOKEN={secret}\nOAUTH_ENCRYPTION_KEY={secret}\nREED_API_KEY={secret}\nDATABASE_URL=sqlite:///do-not-open.db\n')
    monkeypatch.setenv('LLM_MODEL','explicit-shell-model')
    monkeypatch.setenv('LLM_API_KEY',secret)
    calls=[]
    def run(command,*,cwd,env):
        calls.append((command,cwd,env))
        assert set(env)=={'PATH','PYTHONUTF8','PYTHONNOUSERSITE','LLM_PROVIDER','LLM_MODEL','LLM_BASE_URL'}
        assert env['LLM_MODEL']=='explicit-shell-model' and env['LLM_PROVIDER']=='ollama'
        assert secret not in str(env) and 'do-not-open' not in str(env)
        report=Path(command[command.index('--output')+1]);report.parent.mkdir();report.write_text('{}')
        return SimpleNamespace(returncode=2)
    monkeypatch.setattr(module.subprocess,'run',run)
    assert module.main()==2
    command,cwd,_=calls[0]
    assert command[1:3]==['-m','app.services.requirements_eval'] and cwd==tmp_path/'apps/api'
    assert 'requirements-review.json' in command[command.index('--review')+1]
    assert '--fail-fast' in command and '--single-attempt' in command
    output=capsys.readouterr().out
    assert '.local/requirements-check-' in output and secret not in output
    assert not (tmp_path/'do-not-open.db').exists()


def test_model_check_missing_dependencies_reports_setup_without_launching(tmp_path,monkeypatch,capsys):
    module=launcher(tmp_path,monkeypatch,interpreter=False)
    assert module.main()==2
    assert 'uv sync --frozen' in capsys.readouterr().out


def test_model_check_and_migration_are_mutually_exclusive(tmp_path,monkeypatch):
    module=launcher(tmp_path,monkeypatch)
    monkeypatch.setattr(module.sys,'argv',['scripts/dev.py','--check-model','--migrate'])
    with pytest.raises(SystemExit) as error:module.main()
    assert error.value.code==2


@pytest.mark.parametrize('mode',[[],['--migrate']])
def test_normal_launch_still_runs_app_services_and_only_explicit_migrations(tmp_path,monkeypatch,mode):
    module=launcher(tmp_path,monkeypatch)
    monkeypatch.setattr(module.sys,'argv',['scripts/dev.py',*mode])
    monkeypatch.setenv('APP_ACCESS_TOKEN','synthetic-launcher-token-'*3)
    monkeypatch.setattr(module.signal,'signal',lambda *_:None)
    events=[]
    def run(command,**_):
        events.append(('migration',command));return SimpleNamespace(returncode=0)
    def popen(command,**kwargs):
        events.append(('service',command))
        assert kwargs['env']['APP_ACCESS_TOKEN']=='synthetic-launcher-token-'*3
        return SimpleNamespace(returncode=0,poll=lambda:0,wait=lambda **_:0)
    monkeypatch.setattr(module.subprocess,'run',run)
    monkeypatch.setattr(module.subprocess,'Popen',popen)
    assert module.main()==1  # A service exiting, even cleanly, ends the combined run.
    assert [kind for kind,_ in events]==(['migration'] if mode else [])+['service']*3
    services=[command for kind,command in events if kind=='service']
    assert 'app.main:create_app' in services[0] and 'app.worker.main' in services[1]
    assert services[2]==['npm','run','dev']
    if mode:assert events[0][1][-1]=='app.services.migration_cli'


def test_full_model_diagnostic_is_explicit_and_does_not_add_fast_flags(tmp_path,monkeypatch):
    module=launcher(tmp_path,monkeypatch)
    monkeypatch.setattr(module.sys,'argv',['scripts/dev.py','--check-model-full'])
    calls=[]
    def run(command,**_):calls.append(command);return SimpleNamespace(returncode=1)
    monkeypatch.setattr(module.subprocess,'run',run)
    assert module.main()==1
    assert '--fail-fast' not in calls[0] and '--single-attempt' not in calls[0]


def test_cancelled_model_check_returns_without_starting_services_or_traceback(tmp_path,monkeypatch,capsys):
    module=launcher(tmp_path,monkeypatch)
    def cancelled(*_,**__):raise KeyboardInterrupt
    monkeypatch.setattr(module.subprocess,'run',cancelled)
    assert module.main()==130
    assert 'cancelled' in capsys.readouterr().out


def test_targeted_case_uses_isolated_fast_runner(tmp_path,monkeypatch):
    module=launcher(tmp_path,monkeypatch)
    monkeypatch.setattr(module.sys,'argv',['scripts/dev.py','--check-model','--case','canonical-7661586'])
    calls=[]
    monkeypatch.setattr(module.subprocess,'run',lambda command,**kwargs:(calls.append((command,kwargs)) or SimpleNamespace(returncode=2)))
    assert module.main()==2
    command,kwargs=calls[0]
    assert command[command.index('--case')+1]=='canonical-7661586'
    assert '--fail-fast' in command and '--single-attempt' in command
    assert 'DATABASE_URL' not in kwargs['env'] and 'APP_ACCESS_TOKEN' not in kwargs['env']


@pytest.mark.parametrize("case",["canonical-7661586", ""])
def test_case_selector_requires_model_check_mode(tmp_path,monkeypatch,case):
    module=launcher(tmp_path,monkeypatch)
    monkeypatch.setattr(module.sys,'argv',['scripts/dev.py','--case',case])
    with pytest.raises(SystemExit) as error:module.main()
    assert error.value.code==2


def test_source_check_isolated_environment_and_no_tracker_services(tmp_path,monkeypatch,capsys):
    module=launcher(tmp_path,monkeypatch)
    monkeypatch.setattr(module.sys,'argv',['scripts/dev.py','--check-discovery','lever','--board','fixture','--employer','Fixture'])
    marker='synthetic-private-source-marker'
    monkeypatch.delenv('URL_FETCH_ALLOWED_HOSTS',raising=False)
    (tmp_path/'.env').write_text(f'APP_ACCESS_TOKEN={marker}\nDATABASE_URL=sqlite:///never-open.db\nREED_API_KEY={marker}\nLLM_API_KEY={marker}\nURL_FETCH_ALLOWED_HOSTS=api.lever.co\n')
    calls=[]
    def run(command,*,cwd,env):
        calls.append((command,env))
        assert not {'APP_ACCESS_TOKEN','DATABASE_URL','REED_API_KEY','LLM_API_KEY','OAUTH_ENCRYPTION_KEY'} & env.keys()
        assert env['URL_FETCH_ALLOWED_HOSTS']=='api.lever.co'
        return SimpleNamespace(returncode=2)
    monkeypatch.setattr(module.subprocess,'run',run)
    assert module.main()==2
    command,env=calls[0]
    assert command[1:3]==['-m','app.services.discovery_check']
    assert command[command.index('--provider')+1]=='lever'
    assert marker not in capsys.readouterr().out
    assert not (tmp_path/'never-open.db').exists()


def test_reed_check_forwards_only_its_required_private_key(tmp_path,monkeypatch):
    module=launcher(tmp_path,monkeypatch)
    monkeypatch.setattr(module.sys,'argv',['scripts/dev.py','--check-discovery','reed','--query','graduate technology'])
    monkeypatch.setenv('REED_API_KEY','synthetic-required-reed-key')
    monkeypatch.setenv('LLM_API_KEY','synthetic-excluded-model-key')
    calls=[]
    monkeypatch.setattr(module.subprocess,'run',lambda command,**kwargs:(calls.append((command,kwargs['env'])) or SimpleNamespace(returncode=2)))
    assert module.main()==2
    assert calls[0][1]['REED_API_KEY']=='synthetic-required-reed-key'
    assert 'LLM_API_KEY' not in calls[0][1]


@pytest.mark.parametrize('flags',[
    ['--board','fixture'],['--region','global'],['--employer','Fixture'],['--query','software'],
    ['--check-discovery','lever','--migrate'],['--check-discovery','lever','--case','canonical-7661586'],
    ['--check-model','--check-discovery','lever'],
])
def test_source_flags_cannot_accidentally_start_or_migrate_tracker(tmp_path,monkeypatch,flags):
    module=launcher(tmp_path,monkeypatch)
    monkeypatch.setattr(module.sys,'argv',['scripts/dev.py',*flags])
    monkeypatch.setattr(module.subprocess,'run',lambda *_args,**_kwargs:pytest.fail('No subprocess for invalid mode flags'))
    with pytest.raises(SystemExit) as error:module.main()
    assert error.value.code==2

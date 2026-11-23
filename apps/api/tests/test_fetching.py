"""Controlled HTTP rules/rate checks; no live sites or owner credentials."""
import httpx
import pytest

from app.services import fetching
from app.services.errors import NeedsInput


@pytest.fixture
def network(monkeypatch):
    calls=[]
    clock={'now':1000.0}
    rules={'text':'User-agent: *\nDisallow: /private\n','status':200}
    original=httpx.Client
    def handle(request):
        calls.append((str(request.url),clock['now'],request.headers.get('authorization')))
        if request.url.path=='/robots.txt':
            return httpx.Response(rules['status'],text=rules['text'],headers=rules.get('headers',{}))
        return httpx.Response(200,text='Public vacancy')
    monkeypatch.setattr(fetching,'_last_request',{})
    monkeypatch.setattr(fetching,'_robots_cache',{},raising=False)
    monkeypatch.setattr(fetching,'validate_public_url',lambda url:url)
    monkeypatch.setenv('URL_FETCH_ALLOWED_HOSTS','jobs.example.org,other.example.org,www.reed.co.uk')
    monkeypatch.setattr(fetching,'monotonic',lambda:clock['now'])
    monkeypatch.setattr(fetching,'sleep',lambda seconds:clock.update(now=clock['now']+seconds))
    monkeypatch.setattr(fetching.httpx,'Client',lambda **kwargs:original(transport=httpx.MockTransport(handle),**kwargs))
    return calls,clock,rules


def test_public_batch_reuses_robots_but_keeps_rate_limit_and_path_rules(network):
    calls,clock,rules=network
    assert fetching.fetch_page('https://jobs.example.org/one')=='Public vacancy'
    assert fetching.fetch_page('https://jobs.example.org/two')=='Public vacancy'
    assert [url for url,_,_ in calls]==['https://jobs.example.org/robots.txt','https://jobs.example.org/one','https://jobs.example.org/two']
    assert calls[2][1]-calls[1][1]>=5
    with pytest.raises(NeedsInput,match='robots.txt'):
        fetching.fetch_page('https://jobs.example.org/private')
    assert len(calls)==3


def test_expired_rules_are_refetched_and_new_denial_is_honoured(network):
    calls,clock,rules=network
    fetching.fetch_page('https://jobs.example.org/one')
    clock['now']+=301
    rules['text']='User-agent: *\nDisallow: /\n'
    with pytest.raises(NeedsInput,match='robots.txt'):
        fetching.fetch_page('https://jobs.example.org/two')
    assert [url for url,_,_ in calls][-1]=='https://jobs.example.org/robots.txt'
    assert not any(url.endswith('/two') for url,_,_ in calls)


def test_expired_rules_cannot_fall_back_after_denial(network):
    calls,clock,rules=network
    fetching.fetch_page('https://jobs.example.org/one')
    clock['now']+=301;rules['status']=403
    with pytest.raises(NeedsInput,match='denies access'):
        fetching.fetch_page('https://jobs.example.org/two')
    assert not any(url.endswith('/two') for url,_,_ in calls)


def test_robots_rules_are_scoped_to_scheme_and_host(network):
    calls,clock,rules=network
    for url in ['https://jobs.example.org/one','http://jobs.example.org/one','https://other.example.org/one']:
        fetching.fetch_page(url)
    assert len([url for url,_,_ in calls if url.endswith('/robots.txt')])==3


def test_cached_rules_keep_crawl_delay_and_private_reed_auth_off_robots(network):
    calls,clock,rules=network
    rules['text']='User-agent: *\nAllow: /api/1.0/\nCrawl-delay: 9\n'
    auth=('synthetic-key','')
    fetching.fetch_page('https://www.reed.co.uk/api/1.0/search?keywords=graduate',auth=auth)
    fetching.fetch_page('https://www.reed.co.uk/api/1.0/jobs/123',auth=auth)
    assert len(calls)==3 and calls[0][2] is None
    assert calls[1][2] and calls[2][2] and calls[2][1]-calls[1][1]>=9


def test_cached_permission_does_not_override_removed_host_approval(network,monkeypatch):
    calls,clock,rules=network
    fetching.fetch_page('https://jobs.example.org/one')
    monkeypatch.setenv('URL_FETCH_ALLOWED_HOSTS','')
    with pytest.raises(NeedsInput,match='not enabled'):
        fetching.fetch_page('https://jobs.example.org/two')
    assert len(calls)==2


@pytest.mark.parametrize('control',['no-store','no-cache','max-age=0','max-age=invalid'])
def test_server_can_disable_robots_reuse(network,control):
    calls,clock,rules=network
    rules['headers']={'Cache-Control':control}
    fetching.fetch_page('https://jobs.example.org/one')
    fetching.fetch_page('https://jobs.example.org/two')
    assert len([url for url,_,_ in calls if url.endswith('/robots.txt')])==2


def test_short_server_lifetime_takes_precedence_over_default(network):
    calls,clock,rules=network
    rules['headers']={'Cache-Control':'public, max-age="10"'}
    fetching.fetch_page('https://jobs.example.org/one')
    clock['now']+=11
    fetching.fetch_page('https://jobs.example.org/two')
    assert len([url for url,_,_ in calls if url.endswith('/robots.txt')])==2


def test_cdn_age_does_not_extend_server_robots_lifetime(network):
    calls,clock,rules=network
    rules['headers']={'Cache-Control':'max-age=10','Age':'9'}
    fetching.fetch_page('https://jobs.example.org/one')
    fetching.fetch_page('https://jobs.example.org/two')
    assert len([url for url,_,_ in calls if url.endswith('/robots.txt')])==2

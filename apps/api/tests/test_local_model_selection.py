"""A loopback Ollama endpoint may still refer to a remotely hosted model."""
import json

import httpx
import pytest

from app.integrations.llm.provider import Ollama
from app.services import requirements
from app.services.errors import NeedsInput


@pytest.mark.parametrize("protocol", ["native", "compatible"])
@pytest.mark.parametrize("selection,metadata", [
    ("glm-5.3-flash:cloud", None),
    ("gpt-oss:120b-cloud", None),
    ("my-local-alias", {"remote_host": "https://ollama.com", "remote_model": "remote-private-marker"}),
    ("my-local-alias", {"model_info": {"general.architecture": "qwen2"}, "remote_host": "https://ollama.com"}),
    ("my-local-alias", {}),
    ("my-local-alias", {"model_info": None}),
])
def test_cloud_or_unverifiable_selection_never_receives_source(monkeypatch, protocol, selection, metadata):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_MODEL", selection)
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:11434/v1")
    calls = []
    marker = "SYNTHETIC_JOB_SOURCE_MUST_NOT_BE_SENT"
    def handle(request):
        calls.append(request)
        assert request.url.path == "/api/show", "Only model-name metadata may be requested before locality is checked"
        assert json.loads(request.content) == {"model": selection}
        assert marker.encode() not in request.content
        return httpx.Response(200, json=metadata)
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(NeedsInput) as caught:
            if protocol == "native":
                requirements.extract(marker, client=client, attempts=1)
            else:
                Ollama(selection, client=client).extract("https://example.org/job", marker)
    assert "remote-private-marker" not in str(caught.value)
    assert "ollama.com" not in str(caught.value)
    assert len(calls) == (0 if metadata is None else 1)


@pytest.mark.parametrize("protocol", ["native", "compatible"])
def test_local_metadata_precedes_source_and_does_not_contain_it(monkeypatch, protocol):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_MODEL", "qwen2.5:7b")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:11434/v1")
    calls = []
    source = "Fixture Engineer. Python required."
    def handle(request):
        calls.append(request.url.path)
        body = json.loads(request.content)
        if request.url.path == "/api/show":
            assert body == {"model": "qwen2.5:7b"} and source.encode() not in request.content
            return httpx.Response(200, json={"model_info": {"general.architecture": "qwen2"}})
        assert source in body["messages"][-1]["content"]
        result = {"done": True, "message": {"content": '{"skills": [], "education": [], "experience": []}'}} if protocol == "native" else {"choices": [{"message": {"content": '{"title": "Engineer", "company": "Fixture"}'}}]}
        return httpx.Response(200, json=result)
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        if protocol == "native":
            requirements.extract(source, client=client, attempts=1)
        else:
            Ollama("qwen2.5:7b", client=client).extract("https://example.org/job", source)
    assert calls == ["/api/show", "/api/chat" if protocol == "native" else "/v1/chat/completions"]

"""Frozen real-posting controls; null dates do not establish positive-date quality."""
import json
from pathlib import Path

from app.services.evaluation import baseline, evaluate, load_cases
from app.services.matching import graduate_level

ROOT=Path(__file__).resolve().parents[3]/'fixtures/eval'


def predict(url,html):
    data=baseline(url,html)
    data['graduate']=graduate_level(data['title'],data['description'])
    return data


def test_new_real_control_labels_and_provenance_are_bound_to_stripped_snapshots():
    cases=load_cases(ROOT/'heldout-nov20.json')
    metadata=json.loads((ROOT/'provenance-nov20.json').read_text())
    by_id={row['id']:row for row in metadata['postings']}
    assert len(cases)==3
    for case,html in cases:
        assert by_id[case.id]['excerpt_sha256']==case.sha256
        assert '<form' not in html.lower() and '<script' not in html.lower() and '<button' not in html.lower()
    report=evaluate(cases,predict)
    assert report['extraction_failures']==report['false_confirmed_yes']==0
    assert report['known_labels']['graduate']==3 and report['known_label_accuracy']['graduate']==1
    assert report['known_labels']['deadline']==report['known_labels']['start_date']==0
    assert report['known_label_accuracy']['deadline'] is None and report['phase_2_accepted'] is False


def test_all_thirty_eight_real_posting_regressions():
    cases=load_cases(ROOT/'manifest-nov20.json')
    assert len(cases)==38
    report=evaluate(cases,predict)
    assert report['extraction_failures']==report['false_confirmed_yes']==0
    assert all(report['accuracy'][key]>=.9 for key in ['company','title','location','deadline','start_date','graduate'])
    assert report['known_labels']['start_date']==3 and report['phase_2_accepted'] is False

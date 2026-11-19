import pytest
from app.services.extraction import labelled_date


@pytest.mark.parametrize('text', [
    'Start Date: September 6th 2027', 'Start date: September 6, 2027',
    'Start date: September 6th, 2027', 'Start date: September 6th,2027', 'Start date: 6th September 2027',
    'Start date: 6 September 2027', 'START DATE: september 6 2027',
])
def test_full_labelled_dates_in_both_orders(text):
    assert labelled_date(text, 'Start date').isoformat() == '2027-09-06'


@pytest.mark.parametrize('text', [
    'Start Date: September 2027', 'Start Date: September 6th',
    'Start Date: Flexible between January and September 2027',
    'Start Date: September 6th 2027 or September 7th 2027',
    'Start Date: 6 September 2027 to 8 September 2027',
    'Start Date: 6 September 2027 – 8 September 2027',
    'Start Date: September 6th 2027 – September 8th 2027',
    'Start Date: 6 September 2027 – 18 September 2027',
    'Start Date: September 6th 2027–2028',
    'Start Date: February 30th 2027', 'Start Date: February 29th 2027',
    'Restart date: September 6th 2027', 'Start Date: September 6th–8th 2027',
])
def test_partial_impossible_and_range_dates_stay_unknown(text):
    assert labelled_date(text, 'Start date') is None


def test_deadline_and_start_labels_do_not_leak_into_each_other():
    text = 'Application deadline: Midnight, 29th November 2026. Start date: September 6th 2027.'
    assert labelled_date(text, r'Applications? deadline').isoformat() == '2026-11-29'
    assert labelled_date(text, 'Start date').isoformat() == '2027-09-06'

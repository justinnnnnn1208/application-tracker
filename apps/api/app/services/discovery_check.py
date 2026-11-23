"""Read public discovery adapters without tracker services, imports or model calls."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from time import monotonic

from app.integrations.discovery import ashby, greenhouse, lever, reed, smartrecruiters
from app.services.errors import NeedsInput

PROVIDERS = ('greenhouse', 'lever', 'ashby', 'smartrecruiters', 'reed')


def check(provider, *, board='', employer='', region='global', query=''):
    if provider not in PROVIDERS or region not in {'global', 'eu'}:
        raise ValueError('Choose a supported public source and region.')
    if provider != 'lever' and region != 'global':
        raise ValueError('Region applies only to Lever.')
    if provider == 'reed':
        if board or employer or not query.strip() or len(query) > 300:
            raise ValueError('Reed needs public search keywords, not board/employer fields.')
    else:
        greenhouse.validate_board(board)
        if query or len(employer) > 200 or provider != 'greenhouse' and not employer.strip():
            raise ValueError('Use a board slug and the public employer name, not search keywords.')
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'provider': provider,
              'board': board, 'employer': employer.strip(), 'region': region,
              'state': 'NOT TESTED', 'phase_2_accepted': False, 'quality_assessed': False,
              'limits': ['Public adapter compatibility only, not hand-labelled field accuracy or model quality.',
                         'No tracker database/services/imports, OAuth, profile/CV/facts or application forms.',
                         'Existing host approval, robots, limits and delays apply; no settings changed.',
                         'SmartRecruiters/Reed read the first20 details; other ATS read their bounded full board.']}
    readers = {'greenhouse': lambda: greenhouse.read_board(board),
               'lever': lambda: lever.read_board(board, employer.strip(), region),
               'ashby': lambda: ashby.read_board(board, employer.strip()),
               'smartrecruiters': lambda: smartrecruiters.read_board(board, employer.strip()),
               'reed': lambda: reed.read_search(query)}
    started = monotonic()
    try:
        jobs, skipped = readers[provider]()
    except NeedsInput:
        # Adapter errors are deliberately not copied: no response/config bodies.
        report.update(error='Source unavailable. Check existing host approval, source terms, access and private provider configuration. No import or retry attempted.')
    else:
        report.update(state='COMPLETED' if jobs else 'NOT TESTED', postings_read=len(jobs), skipped=skipped,
                      descriptions_present=sum(bool(job.description.strip()) for job in jobs),
                      samples=[{**{key: getattr(job, key) for key in ('url', 'company', 'title', 'location', 'deadline', 'start_date')},
                                'description_chars': len(job.description),
                                'description_sha256': hashlib.sha256(job.description.encode()).hexdigest()}
                               for job in jobs[:20]])
    report['elapsed_seconds'] = round(monotonic() - started, 2)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', choices=PROVIDERS, required=True)
    parser.add_argument('--board', default='')
    parser.add_argument('--employer', default='')
    parser.add_argument('--region', choices=('global', 'eu'), default='global')
    parser.add_argument('--query', default='')
    parser.add_argument('--output', type=Path, required=True, help='New ignored report path; never overwrite an existing report')
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError('Output exists')
        print('Checking public source; no tracker services, database imports or model calls. Keep this terminal open; Control+C cancels.', flush=True)
        report = check(args.provider, board=args.board, employer=args.employer, region=args.region, query=args.query)
        args.output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with args.output.open('x', encoding='utf-8') as file:
            file.write(json.dumps(report, indent=2, default=str) + '\n')
        args.output.chmod(0o600)
    except KeyboardInterrupt:
        print('Source check cancelled; no tracker import or services started.')
        return 130
    except (OSError, ValueError):
        print('NOT TESTED: check public source arguments and use a new report filename. No tracker import attempted.')
        return 2
    print(f"{report['state']}: {report.get('postings_read', 0)} postings returned; {report.get('skipped', 0)} skipped; {report['elapsed_seconds']}s. Phase 2 acceptance remains unassessed.")
    return 0 if report['state'] == 'COMPLETED' else 2


if __name__ == '__main__':
    raise SystemExit(main())

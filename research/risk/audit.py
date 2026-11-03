"""Aggregate public-source audits; raw observations are never copied to reports."""
from collections import Counter
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def storm_audit(data: bytes) -> dict:
    rows = csv.DictReader(io.StringIO(gzip.decompress(data).decode('utf-8-sig')))
    required = {'STATE_FIPS','CZ_FIPS','CZ_TYPE','EPISODE_ID','EVENT_ID',
                'BEGIN_DATE_TIME','END_DATE_TIME','CZ_TIMEZONE','YEAR'}
    if not required <= set(rows.fieldnames or []):
        raise ValueError('Storm payload schema mismatch')
    count = 0; ids = set(); duplicate = 0; zones = Counter(); years = Counter()
    selected = Counter(); county_codes = {'39':set(),'42':set()}; episodes = {'39':set(),'42':set()}
    missing = Counter(); timezones = Counter()
    for r in rows:
        count += 1
        if r['EVENT_ID'] in ids: duplicate += 1
        ids.add(r['EVENT_ID']); zones[r['CZ_TYPE']] += 1; years[r['YEAR']] += 1
        for field in required:
            if not r[field].strip(): missing[field] += 1
        if r['STATE_FIPS'] in county_codes:
            state=r['STATE_FIPS'];selected[state+':'+r['CZ_TYPE']] += 1
            timezones[r['CZ_TIMEZONE']] += 1
            if r['CZ_TYPE']=='C':
                county_codes[state].add(r['CZ_FIPS']);episodes[state].add(r['EPISODE_ID'])
    return {'rows':count,'duplicate_event_ids':duplicate,'zone_types':dict(sorted(zones.items())),
            'years':dict(years),'missing_required':dict(sorted(missing.items())),
            'selected_state_zone_rows':dict(sorted(selected.items())),
            'reported_county_codes':{s:len(v) for s,v in county_codes.items()},
            'reported_episode_ids_in_county_rows':{s:len(v) for s,v in episodes.items()},
            'selected_timezones':dict(sorted(timezones.items())),
            'limitation':'Reported county codes/episode IDs are not validated outage coverage or independent final evaluation clusters.'}


def audit(cache: Path) -> dict:
    access=json.loads((cache/'access.json').read_text())
    records={r['id']:r for r in access['records']}
    if len(records)!=len(access['records']):raise ValueError('Duplicate access record')
    for r in records.values():
        if r['file'] is not None:
            if Path(r['file']).name!=r['file']:raise ValueError('Invalid cached filename')
            file=cache/r['file']
            if sha(file)!=r['sha256'] or file.stat().st_size!=r['bytes']:
                raise ValueError('Cached response changed')
    attrs=json.loads((cache/records['ornl_datacite']['file']).read_text())['data']['attributes']
    storms={}
    for key in ('noaa_2018','noaa_2022'):
        if records[key]['status']!=200: raise ValueError('NOAA payload unavailable')
        storms[key]=storm_audit((cache/records[key]['file']).read_bytes())
    return {'version':'risk-source-audit-v1','access_manifest_sha256':sha(cache/'access.json'),
            'responses':access['records'], 'ornl_datacite_rights':attrs.get('rightsList'),
            'noaa':storms, 'outage_payload_acquired':False,
            'county_time_outage_coverage':None, 'eligible_outage_labels':None,
            'note':'Access records prove responses, not dataset permission. No EAGLE-I observation file was acquired; null does not mean zero eligible windows exist.'}

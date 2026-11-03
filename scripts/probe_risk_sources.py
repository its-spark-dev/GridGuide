"""Bounded anonymous public-source probes. Raw bytes stay in ignored storage.

No credentials, training, implicit retries or observation extraction from HTML.
Re-running probes observes current upstream state; it is not numerical reproduction.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
NOAA = 'https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/'
SOURCES = {
    'ornl_catalog': 'https://doi.ccs.ornl.gov/dataset/ccec86f0-e144-5de8-aee0-fb26028b26e1',
    'ornl_datacite': 'https://api.datacite.org/dois/10.13139/ORNLNCCS/1975202',
    'ornl_globus': 'https://app.globus.org/file-manager?origin_id=57618e0a-2c99-45ff-9694-24141b92fa17&origin_path=%2F%2Fgen101%2Fworld-shared%2Fdoi-data%2FORNLNCCS%2F202305%2F10.13139_ORNLNCCS_1975202%2F',
    'ornl_listing': 'https://transfer.api.globus.org/v0.10/operation/57618e0a-2c99-45ff-9694-24141b92fa17/ls?path=%2F%2Fgen101%2Fworld-shared%2Fdoi-data%2FORNLNCCS%2F202305%2F10.13139_ORNLNCCS_1975202%2F',
    'noaa_metadata': 'https://www.ncei.noaa.gov/metadata/geoportal/rest/metadata/item/gov.noaa.ncdc:C00510/html',
    'noaa_policy': 'https://www.ncei.noaa.gov/sites/default/files/2023-12/NCEI%20PD-10-2-02%20-%20Open%20Data%20Policy%20Signed.pdf',
    'noaa_index': NOAA,
    'noaa_2018': NOAA+'StormEvents_details-ftp_v1.0_d2018_c20260323.csv.gz',
    'noaa_2022': NOAA+'StormEvents_details-ftp_v1.0_d2022_c20260625.csv.gz',
    'doe_program': 'https://doe417.energy.gov/',
    'doe_summary': 'https://doe417.energy.gov/annual_summary.aspx',
}


def probe(directory):
    directory = directory.resolve()
    if not directory.is_relative_to((ROOT/'data/external/phase4').resolve()):
        raise ValueError('Downloads must remain under ignored data/external/phase4')
    directory.mkdir(parents=True, exist_ok=False)
    records = []
    for key, url in SOURCES.items():
        record = {'id': key, 'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
                  'status': None, 'sha256': None, 'bytes': None, 'file': None}
        try:
            try:
                response = urlopen(Request(url, headers={'User-Agent': 'GridGuide-public-research/1.0'}), timeout=25)
            except HTTPError as error:
                response = error
            with response:
                data = response.read(30_000_001)
                if len(data)>30_000_000:
                    raise ValueError('Response exceeds 30 MB probe cap')
                name=key+'.response'
                (directory/name).write_bytes(data)
                record.update(status=response.status, final_url=response.url,
                              content_type=response.headers.get('Content-Type'), file=name,
                              bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        except (OSError, URLError, ValueError) as error:
            record['error_type']=type(error).__name__
        records.append(record)
        print(key, record['status'], record['bytes'], flush=True)
    manifest={'version':'risk-access-v1','records':records}
    (directory/'access.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    probe(p.parse_args().output)

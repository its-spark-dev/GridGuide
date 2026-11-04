"""Fail on undispositioned findings; accepted reachability analysis is in the G8 packet.

This is not a claim of zero vulnerabilities. Duplicate advisory records are counted
once by ID; alias IDs are accepted only for the explicitly reviewed package/version.
"""
import json
import sys

ACCEPTED = {
 'PYSEC-2026-161','X41-2026-002','GHSA-86qp-5c8j-p5mr','CVE-2026-48710',
 'PYSEC-2026-2281','CVE-2026-48818','GHSA-wqp7-x3pw-xc5r',
 'PYSEC-2026-2280','GHSA-x746-7m8f-x49c','CVE-2026-48817',
 'PYSEC-2026-249','CVE-2026-54283','GHSA-82w8-qh3p-5jfq',
 'PYSEC-2026-248','GHSA-jp82-jpqv-5vv3','CVE-2026-54282',
}
python = json.load(open(sys.argv[1]))
seen = set()
for dependency in python['dependencies']:
    if dependency.get('skip_reason'): raise SystemExit('Unassessed Python dependency')
    for issue in dependency['vulns']:
        assert dependency['name'] == 'starlette' and dependency['version'] == '0.49.3', 'New affected dependency'
        assert issue['id'] in ACCEPTED, 'New Python advisory requires review'
        seen.add(issue['id'])
npm = json.load(open(sys.argv[2]))
assert 'error' not in npm and 'vulnerabilities' in npm, 'npm audit unavailable'
for name, issue in npm['vulnerabilities'].items():
    assert name in {'minimatch','@redocly/openapi-core','openapi-typescript'}, 'New npm affected package'
    assert issue['severity'] in {'low','moderate'}, 'Severe npm finding requires review'
    for via in issue['via']:
        if isinstance(via, dict):
            assert via['url'] == 'https://github.com/advisories/GHSA-g3hv-75wg-m249', 'New npm advisory'
print(json.dumps({'disposition':'Reviewed findings remain; not a zero-vulnerability claim',
                  'python_advisory_ids':sorted(seen),'npm_affected_packages':sorted(npm['vulnerabilities'])}))

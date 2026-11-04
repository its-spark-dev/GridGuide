"""Input-only dataset freezing and verified partition access. No policy imports."""
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path

from benchmarks.contracts import canonical
from .contracts import GENERATOR_VERSION, MLCase, digest, input_eligibility
from .generator import PARTITIONS, generate_suite


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_cases(cases: list[MLCase]) -> dict:
    """Reject input identity/config/topology leakage, preserving related crew variants."""
    if not cases:
        raise ValueError('Empty dataset')
    groups: dict[str, list[MLCase]] = defaultdict(list)
    ids, fingerprints, graph_owners, config_owners = set(), set(), {}, {}
    for raw_case in cases:
        case = MLCase.model_validate(raw_case.model_dump())
        if case.case_id in ids or case.fingerprint in fingerprints:
            raise ValueError('Duplicate case')
        ids.add(case.case_id)
        fingerprints.add(case.fingerprint)
        groups[case.group_id].append(case)
        if graph_owners.setdefault(case.graph_hash, case.group_id) != case.group_id:
            raise ValueError('Duplicate/isomorphic topology across groups')
        config_key = digest(case.configuration.model_dump(mode='json'))
        if config_owners.setdefault(config_key, case.group_id) != case.group_id:
            raise ValueError('Related configuration across groups')
    for group in groups.values():
        if len({c.partition for c in group}) != 1:
            raise ValueError('Related graph family crosses partitions')
        if len({c.graph_hash for c in group}) != 1 or len({c.configuration for c in group}) != 1:
            raise ValueError('Inconsistent group lineage')
        if sorted(len(c.problem.crews) for c in group) != [1, 2, 4]:
            raise ValueError('Incomplete or duplicate crew variants')
        base = group[0].problem
        if any(c.problem.tasks != base.tasks or c.problem.groups != base.groups for c in group):
            raise ValueError('Unrecorded task/customer change within group')
    counts = Counter(c.partition for c in cases)
    return {'status': 'PASS', 'cases': len(cases), 'groups': len(groups),
            'unique_graph_hashes': len(graph_owners), 'partition_counts': dict(sorted(counts.items())),
            'partition_groups': {p: sum(g[0].partition == p for g in groups.values()) for p in PARTITIONS},
            'input_complete_scope': {p: sum(input_eligibility(c.problem)['complete_customer_scope']
                                          for c in cases if c.partition == p) for p in PARTITIONS},
            'incomplete_modes': dict(sorted(Counter(c.configuration.incomplete_mode for c in cases).items())),
            'family_counts': dict(sorted(Counter(c.configuration.mechanism for c in cases).items())),
            'topology_check': 'directed-color-refinement-v1; conservative isomorphism exclusion, not semantic independence'}


def write_dataset(output: Path, profile: str = 'full', source_revision: str = 'unrecorded') -> dict:
    """Create immutable input artifacts. Final outcomes do not exist at this stage."""
    output = Path(output)
    if output.exists():
        raise FileExistsError('Dataset output already exists; freeze is never overwritten')
    if source_revision == 'unrecorded' or len(source_revision) != 40:
        raise ValueError('Record the full source revision before freezing inputs')
    cases = generate_suite(profile)
    audit = audit_cases(cases)
    manifest = {'version': 'ml-dataset-manifest-v1', 'generator_version': GENERATOR_VERSION,
                'profile': profile, 'source_revision': source_revision, 'audit': audit,
                'partition_files': {}, 'cases': [], 'groups': {},
                'source_files': {name: file_hash(Path(__file__).with_name(name))
                                 for name in ('contracts.py', 'generator.py', 'dataset.py')},
                'holdout_status': 'inputs-only; no policy labels or metrics generated',
                'split_rule': 'whole graph/customer/configuration group, including all 1/2/4-crew variants',
                'provenance': 'independently authored fictional assumptions; no AEP/raw data dependency'}
    output.mkdir(parents=True)
    for partition in PARTITIONS:
        selected = [c for c in cases if c.partition == partition]
        payload = b''.join(canonical(c.model_dump(mode='json')) + b'\n' for c in selected)
        filename = f'{partition}.jsonl.gz'
        compressed = gzip.compress(payload, mtime=0)
        (output/filename).write_bytes(compressed)
        manifest['partition_files'][partition] = {'file': filename,
            'sha256': hashlib.sha256(compressed).hexdigest(),
            'content_sha256': hashlib.sha256(payload).hexdigest(), 'cases': len(selected)}
    for case in cases:
        manifest['cases'].append({'case_id': case.case_id, 'partition': case.partition,
            'group_id': case.group_id, 'fingerprint': case.fingerprint,
            'problem_fingerprint': case.problem.fingerprint, 'graph_hash': case.graph_hash,
            'input_eligibility': input_eligibility(case.problem)})
        manifest['groups'][case.group_id] = {'partition': case.partition, 'graph_hash': case.graph_hash,
                                           'configuration': case.configuration.model_dump(mode='json')}
    manifest['dataset_hash'] = digest(manifest)
    (output/'manifest.json').write_bytes(canonical(manifest)+b'\n')
    return manifest


def read_manifest(root: Path) -> dict:
    manifest = json.loads((Path(root)/'manifest.json').read_text())
    checksum = manifest.get('dataset_hash')
    if checksum != digest({k: v for k, v in manifest.items() if k != 'dataset_hash'}):
        raise ValueError('Dataset manifest checksum mismatch')
    if manifest.get('version') != 'ml-dataset-manifest-v1' or manifest.get('generator_version') != GENERATOR_VERSION:
        raise ValueError('Unsupported dataset manifest')
    if set(manifest['partition_files']) != set(PARTITIONS):
        raise ValueError('Dataset partition inventory mismatch')
    return manifest


def load_partition(root: Path, partition: str) -> list[MLCase]:
    """Low-level input reader. Stage-specific training guards live in the workflow."""
    if partition not in PARTITIONS:
        raise ValueError('Unknown partition')
    root = Path(root)
    manifest = read_manifest(root)
    item = manifest['partition_files'][partition]
    if item['file'] != f'{partition}.jsonl.gz':
        raise ValueError('Unsafe/noncanonical partition path')
    path = root/item['file']
    if file_hash(path) != item['sha256']:
        raise ValueError('Partition checksum mismatch')
    payload = gzip.decompress(path.read_bytes())
    if hashlib.sha256(payload).hexdigest() != item['content_sha256']:
        raise ValueError('Partition content checksum mismatch')
    cases = [MLCase.model_validate_json(line) for line in payload.splitlines()]
    expected = [c for c in manifest['cases'] if c['partition'] == partition]
    if len(cases) != item['cases'] or len(cases) != len(expected):
        raise ValueError('Partition case count mismatch')
    for case, record in zip(cases, expected):
        if case.partition != partition or case.fingerprint != record['fingerprint']:
            raise ValueError('Partition case lineage mismatch')
    return cases

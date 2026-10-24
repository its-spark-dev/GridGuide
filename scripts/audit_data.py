#!/usr/bin/env python3
"""Read-only challenge-data audit; emits aggregates, never customer/contact values.

Inspection dependencies: pyshp, pyproj, shapely, openpyxl. No extraction or network.
Run: python scripts/audit_data.py --output /tmp/gridguide-audit.json
This is an inspection utility, not the product's preprocessing/analytics pipeline.
"""
import argparse
from collections import Counter, defaultdict
import datetime
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import statistics
import sys
import xml.etree.ElementTree as ET
import zipfile

import openpyxl
from pyproj import CRS, Geod, Transformer
import shapefile
from shapely.geometry import shape


KEEP = {
    'id', 'premise_nu', 'aep_xfmr_l', 'aep_locati', 'circuit_id', 'circuit__1',
    'location_n', 'location_1', 'upstream_l', 'aep_statio', 'aep_circui',
    'device_typ', 'mounting', 'a_phase_sp', 'b_phase_sp', 'c_phase_sp',
    'height', 'Outage_Num', 'Incident_W', 'Event', 'Circuit', 'Substation',
    'Report_Tim', 'Repaired_D', 'Repaired', 'Status', 'Asset_Type',
    'Inform_Wor', 'Access_Iss', 'Special_Eq', 'Longitude', 'Latitude',
    'NEAR_FID', 'NEAR_DIST', 'eo_source_', 'global_id',
}
CATEGORIES = {
    'Event', 'Repaired', 'Status', 'Asset_Type', 'Inform_Wor', 'Access_Iss',
    'Special_Eq', 'device_typ', 'mounting', 'network_ty', 'status', 'normal_sta',
}


def blank(v):
    return v is None or (isinstance(v, str) and not v.strip())


def key(v):
    if blank(v):
        return None
    return str(int(v)) if isinstance(v, (int, float)) and v == int(v) else str(v).strip()


def git_blob(b):
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()


def field_stats(values):
    good = [v for v in values if not blank(v)]
    result = {'missing': len(values)-len(good), 'unique_nonmissing': len(set(good))}
    if good and all(isinstance(v, (int, float, datetime.date)) for v in good):
        result.update(min=min(good), max=max(good))
    return result


def audit_layers(raw, result):
    layers = {}
    for name in ('Data1.zip', 'Data2.zip'):
        with zipfile.ZipFile(raw / name) as z:
            result['files'][name]['crc_ok'] = z.testzip() is None
            result['files'][name]['members'] = {n: z.getinfo(n).file_size for n in z.namelist()}
            for n in z.namelist():
                if not n.endswith('.shp'):
                    continue
                stem = n[:-4]
                print('Inspecting', stem, file=sys.stderr)
                r = shapefile.Reader(**{ext: io.BytesIO(z.read(stem+'.'+ext)) for ext in ('shp','shx','dbf')}, encoding='utf-8')
                fields = [f[0] for f in r.fields[1:]]
                records = [x.as_dict() for x in r.iterRecords()]
                crs = CRS.from_wkt(z.read(stem+'.prj').decode())
                horizontal = crs.sub_crs_list[0] if crs.is_compound else crs
                transformer = Transformer.from_crs(horizontal, 4326, always_xy=True)
                bounds = transformer.transform_bounds(*r.bbox)
                cols = {}
                for f, typ, size, dec in r.fields[1:]:
                    values = [x[f] for x in records]
                    cols[f] = {'type': str(typ), 'width': size, 'decimals': dec, **field_stats(values)}
                    if f in CATEGORIES:
                        cols[f]['counts'] = dict(Counter(str(v) for v in values))
                aliases = {}
                metadata = ET.fromstring(z.read(stem+'.shp.xml'))
                for node in metadata.findall('.//attr'):
                    label = node.findtext('attrlabl')
                    if label:
                        aliases[label] = node.findtext('attalias')
                geom_counts = Counter()
                points = []
                for s in r.iterShapes():
                    if not s.points:
                        geom_counts['empty'] += 1
                        points.append(None)
                        continue
                    g = shape(s.__geo_interface__)
                    geom_counts['invalid'] += not g.is_valid
                    geom_counts['zero_length'] += g.geom_type in ('LineString','MultiLineString') and g.length == 0
                    geom_counts[g.geom_type] += 1
                    points.append(tuple(s.points[0][:2]))
                result['layers'][stem] = {'archive': name, 'features': len(r), 'geometry': r.shapeTypeName,
                    'horizontal_crs': horizontal.to_authority(), 'wkt': crs.to_wkt(),
                    'bounds_wgs84': list(bounds), 'fields': cols, 'aliases': aliases,
                    'geometry_checks': dict(geom_counts), 'cpg': z.read(stem+'.cpg').decode()}
                if stem.startswith('arcos'):
                    result['layers'][stem]['duplicate_full_attribute_rows'] = len(records)-len({tuple(x.items()) for x in records})
                layers[stem] = [{k: v for k,v in rec.items() if k in KEEP} | {'xy': xy}
                                for rec,xy in zip(records,points)]
    return layers


def audit_topology(raw, layers, result):
    with zipfile.ZipFile(raw/'matched_upstream.zip') as z:
        result['files']['matched_upstream.zip']['crc_ok'] = z.testzip() is None
        result['files']['matched_upstream.zip']['members'] = {n:z.getinfo(n).file_size for n in z.namelist()}
        lines = z.read('matched_upstream.txt').decode('utf-8-sig').splitlines()
    paths = defaultdict(list)
    nodes = {}
    parents = defaultdict(set)
    malformed = repeated = 0
    conflicting_node_metadata = set()
    for line in lines:
        if not line.strip():
            continue
        tokens = line.split('\t')
        parsed = [t.split('*') for t in tokens[1:]]
        if len(tokens)<2 or any(len(t)!=4 for t in parsed):
            malformed += 1
            continue
        path = [(t[0], t[1]) for t in parsed]
        repeated += len(path) != len(set(path))
        paths[tokens[0]].append(path)
        for t in parsed:
            if (t[0],t[1]) in nodes and nodes[(t[0],t[1])] != (t[2],t[3]):
                conflicting_node_metadata.add((t[0],t[1]))
            nodes[(t[0],t[1])] = (t[2],t[3])
        for child,parent in zip(path,path[1:]):
            parents[child].add(parent)
    # Kahn's algorithm: audit union graph, including references without GIS geometry.
    indegree = Counter({n:0 for n in nodes})
    for pp in parents.values():
        for p in pp:
            indegree[p]+=1
    queue=[n for n in nodes if indegree[n]==0]
    visited=0
    while queue:
        n=queue.pop(); visited+=1
        for p in parents[n]:
            indegree[p]-=1
            if indegree[p]==0: queue.append(p)
    cus=layers['Customer_Clip']
    gis_premises=Counter(key(c['premise_nu']) for c in cus)
    sets={ln:{key(r['id']) for r in rr if 'id' in r} for ln,rr in layers.items()}
    lookups={ln:{key(r['id']):r for r in rr if 'id' in r} for ln,rr in layers.items()}
    matches={}
    match_node={}
    for n,(_,loc) in nodes.items():
        candidates = (['Transformer_Clip'] if n[0]=='eo_power_xfrmr_inst' else
                      ['Fuse_Bank_Clip','Recloser_Bank_Clip','Switch_Clip'] if n[0]=='eo_isolating_eqpt_inst' else [])
        hits=[ln for ln in candidates if n[1] in sets[ln]]
        match_node[n]=hits
    for typ in sorted(set(n[0] for n in nodes)):
        nn=[n for n in nodes if n[0]==typ]
        matches[typ]={'unique_nodes':len(nn), 'id_matches':sum(bool(match_node[n]) for n in nn),
                     'ambiguous_layer_matches':sum(len(match_node[n])>1 for n in nn),
                     'location_agrees_with_id':sum(len(match_node[n])==1 and key(lookups[match_node[n][0]][n[1]].get('location_n'))==nodes[n][1] for n in nn)}
    stats=Counter()
    examples=[]
    for c in cus:
        p=paths.get(key(c['premise_nu']),[])
        if not p: continue
        stats['customer_rows_with_path']+=1
        unique={tuple(pp) for pp in p}
        if len(unique)!=1:
            stats['customer_rows_ambiguous_path']+=1; continue
        path=list(next(iter(unique)))
        xf=path[0]
        if xf[0]=='eo_power_xfrmr_inst' and len(match_node[xf])==1:
            stats['customer_rows_first_transformer_matches_id']+=1
            t=lookups['Transformer_Clip'][xf[1]]
            stats['customer_transformer_location_agrees'] += key(c.get('aep_xfmr_l'))==key(t.get('location_n'))
            stats['customer_transformer_circuit_agrees'] += key(c.get('circuit_id'))==key(t.get('circuit_id'))
        unresolved=[n for n in path if n[0]!='eo_circuit' and len(match_node[n])!=1]
        if not unresolved:
            stats['customer_rows_all_noncircuit_nodes_resolve']+=1
            if any(nodes[n][0]=='Fuse' for n in path) and len(examples)<5:
                examples.append({'customer_dbf_row_1based':cus.index(c)+1,
                    'path_types':[nodes[n][0] for n in path],
                    'path_node_count':len(path), 'circuit':c.get('circuit_id'),
                    'unique_customer_premise':gis_premises[key(c['premise_nu'])]==1,
                    'all_nodes_single_parent':all(len(parents[n])<=1 for n in path),
                    'transformer_location_agrees':key(c.get('aep_xfmr_l'))==nodes[path[0]][1]})
    result['topology']={
        'nonblank_lines':sum(bool(x.strip()) for x in lines),'blank_lines':sum(not x.strip() for x in lines),
        'malformed_lines':malformed,'premises':len(paths),'duplicate_premise_lines':sum(len(v)-1 for v in paths.values()),
        'conflicting_premise_paths':sum(len({tuple(p) for p in v})>1 for v in paths.values()),
        'premises_with_leading_zero':sum(k.startswith('0') for k in paths),
        'unique_nodes':len(nodes),'unique_edges':sum(len(v) for v in parents.values()),
        'nodes_multiple_parents':sum(len(v)>1 for v in parents.values()),
        'union_graph_is_dag':visited==len(nodes),'paths_with_repeated_nodes':repeated,
        'nodes_with_conflicting_metadata':len(conflicting_node_metadata),
        'path_lengths':dict(Counter(len(v[0]) for v in paths.values())),
        'types':dict(Counter(v[0] for v in nodes.values())), 'join_by_entity_type':matches,
        'gis_unique_premises_in_topology':len(set(gis_premises)&set(paths)),
        'topology_premises_not_in_gis':len(set(paths)-set(gis_premises)),
        'gis_premise_duplicate_excess':sum(v-1 for k,v in gis_premises.items() if k),
        'coverage':dict(stats), 'candidate_demo_rows':examples,
    }
    missing_types=Counter()
    fallback=Counter()
    for n,hits in match_node.items():
        if hits or n[0]=='eo_circuit': continue
        typ,loc=nodes[n]
        missing_types[typ]+=1
        candidates = ['Transformer_Clip'] if n[0]=='eo_power_xfrmr_inst' else ['Fuse_Bank_Clip','Recloser_Bank_Clip','Switch_Clip']
        hits_by_location=[r for ln in candidates for r in layers[ln] if key(r.get('location_n'))==loc and r.get('device_typ')==typ]
        fallback['unique_typed_location']+=len(hits_by_location)==1
        fallback['ambiguous_typed_location']+=len(hits_by_location)>1
        fallback['no_typed_location']+=not hits_by_location
    result['topology']['unresolved_id_node_types']=dict(missing_types)
    result['topology']['unresolved_id_location_fallback']=dict(fallback)
    result['topology']['customer_rows_circuit_terminal_agrees']=sum(
        bool(paths.get(key(c['premise_nu']))) and nodes[paths[key(c['premise_nu'])][0][-1]][1]==key(c['circuit_id']) for c in cus)
    mapping=defaultdict(set)
    stations=defaultdict(set)
    for ln,rows in layers.items():
        for r in rows:
            if not blank(r.get('aep_circui')) and not blank(r.get('circuit_id')):
                mapping[r['aep_circui']].add(r['circuit_id'])
                stations[r['aep_circui']].add(r.get('aep_statio'))
    result['crosswalk']={'circuit_aliases':len(mapping),'aliases_with_multiple_ids':sum(len(v)>1 for v in mapping.values()),
        'aliases_with_multiple_stations':sum(len(v)>1 for v in stations.values()),
        'ambiguous_aliases':sorted(k for k,v in mapping.items() if len(v)>1),
        'damage_rows_unmapped':sum(r['Circuit'] not in mapping for r in layers['arcos_prod_damage_09_28_Clip'])}
    reverse_mapping=defaultdict(set)
    for alias,ids in mapping.items():
        for cid in ids: reverse_mapping[cid].add(alias)
    result['crosswalk']['ids_with_multiple_aliases']=sum(len(v)>1 for v in reverse_mapping.values())
    demo=cus[1076]
    demo_path=paths[key(demo['premise_nu'])][0]
    demo_xf=lookups['Transformer_Clip'][demo_path[0][1]]
    demo_fuse=lookups['Fuse_Bank_Clip'][demo_path[1][1]]
    alias=demo_xf['aep_circui']
    result['golden_candidate']={
        'customer_dbf_row_1based':1077, 'path_types':[nodes[n][0] for n in demo_path],
        'all_noncircuit_nodes_resolved':all(len(match_node[n])==1 for n in demo_path if n[0]!='eo_circuit'),
        'all_nodes_single_parent':all(len(parents[n])<=1 for n in demo_path),
        'customer_transformer_location_agrees':demo['aep_xfmr_l']==demo_xf['location_n'],
        'customer_transformer_terminal_circuit_agrees':demo['circuit_id']==demo_xf['circuit_id']==nodes[demo_path[-1]][1],
        'circuit_crosswalk_unambiguous':len(mapping[alias])==1 and len(reverse_mapping[demo['circuit_id']])==1,
        'transformer_mounting':demo_xf['mounting'],
        'transformer_phase_specs':{f:demo_xf[f] for f in ('a_phase_sp','b_phase_sp','c_phase_sp')},
        'historical_damage_records_same_alias':sum(r['Circuit']==alias for r in layers['arcos_prod_damage_09_28_Clip']),
        'transformer_upstream_matches_fuse_location':demo_xf['upstream_l']==demo_fuse['location_n'],
        'fuse_upstream_is_circuit_sentinel':demo_fuse['upstream_l']=='CIRCUIT' and demo_path[-1][0]=='eo_circuit',
        'transformer_fuse_distance_m':Geod(ellps='WGS84').inv(*demo_xf['xy'],*demo_fuse['xy'])[2],
    }
    # Compare per-path immediate upstream location with the source GIS field; never patch edges.
    checks=Counter()
    for child,pp in parents.items():
        if len(pp)!=1 or len(match_node.get(child,[]))!=1: continue
        rec=lookups[match_node[child][0]][child[1]]
        upstream=key(rec.get('upstream_l'))
        if upstream:
            checks['comparable_child_edges']+=1
            parent=next(iter(pp))
            checks['upstream_location_agrees']+=upstream==nodes[parent][1]
            checks['terminal_circuit_sentinel']+=parent[0]=='eo_circuit' and upstream=='CIRCUIT'
            checks['semantic_disagreement']+=not(upstream==nodes[parent][1] or (parent[0]=='eo_circuit' and upstream=='CIRCUIT'))
    result['topology']['upstream_field_checks']=dict(checks)
    # Dataset-to-dataset joins: count rows, retaining duplicate match ambiguity.
    joins={}
    for src,sf,dst,df in [
        ('Customer_Clip','aep_xfmr_l','Transformer_Clip','location_n'),
        ('Transformer_Clip','upstream_l','Fuse_Bank_Clip','location_n'),
        ('arcos_prod_damage_09_28_Clip','Circuit','Primary_ExportFeatures','circuit_id'),
        ('arcos_prod_damage_09_28_Clip','Circuit','Primary_ExportFeatures','aep_circui'),
        ('arcos_prod_damage_09_28_Clip','NEAR_FID','Pole_Clip','id'),
        ('arcos_prod_damage_09_28_Clip','NEAR_FID','Primary_ExportFeatures','id')]:
        target=Counter(key(r.get(df)) for r in layers[dst] if not blank(r.get(df)))
        source=[key(r.get(sf)) for r in layers[src]]
        joins[f'{src}.{sf} -> {dst}.{df}']={'rows':len(source),'matched_rows':sum(s in target for s in source),'unique_target_match_rows':sum(target[s]==1 for s in source)}
    result['joins']=joins
    result['circuit_sets']={ln:{f:len({key(r.get(f)) for r in rows if not blank(r.get(f))}) for f in ('circuit_id','aep_circui','Circuit','aep_statio') if f in rows[0]} for ln,rows in layers.items()}


def audit_damage(layers,result):
    rows=layers['arcos_prod_damage_09_28_Clip']
    stats=Counter()
    stats['duplicate_inspected_fields_excess']=len(rows)-len({tuple(sorted(r.items())) for r in rows})
    stats['duplicate_xy_excess']=len(rows)-len({r['xy'] for r in rows})
    for r in rows:
        a,b=r['Report_Tim'],r['Repaired_D']
        if a and b:
            stats['repair_before_report']+=b<a
            stats['repair_equals_report']+=b==a
            stats['repair_after_report']+=b>a
        stats['not_repaired_with_repair_date']+=r['Repaired']=='No' and bool(b)
        stats['geometry_attribute_coordinate_mismatch_1e_6']+= bool(r['xy']) and max(abs(r['xy'][0]-r['Longitude']),abs(r['xy'][1]-r['Latitude']))>1e-6
    stats['zero_outage_num']=sum(r['Outage_Num']==0 for r in rows)
    stats['zero_incident_w']=sum(r['Incident_W']==0 for r in rows)
    result['damage']={'checks':dict(stats),'report_date_counts':dict(Counter(str(r['Report_Tim']) for r in rows)),
        'repair_date_counts':dict(Counter(str(r['Repaired_D']) for r in rows)),
        'asset_work_counts':dict(Counter(str((r['Asset_Type'],r['Inform_Wor'])) for r in rows))}


def audit_workbook(raw,result):
    path=raw/'Install_Labor_HackOHIO.xlsx'
    wf=openpyxl.load_workbook(path,data_only=False)
    wv=openpyxl.load_workbook(path,data_only=True)
    out={}
    for s in wf:
        out[s.title]={'rows':s.max_row,'columns':s.max_column,
            'nonempty_cells':sum(c.value is not None for row in s for c in row),
            'formulas':{c.coordinate:{'formula':c.value,'cached':wv[s.title][c.coordinate].value} for row in s for c in row if c.data_type=='f'},
            'cells':{c.coordinate:c.value for row in s for c in row if c.value is not None}}
    cnc=list(wv['CNC'].iter_rows(min_row=2,max_row=96,min_col=1,max_col=3,values_only=True))
    out['CNC']['independent_summary']={'count':len(cnc),'duplicate_codes':len(cnc)-len({r[0] for r in cnc}),
        'mean_install':statistics.mean(r[1] for r in cnc),'mean_remove':statistics.mean(r[2] for r in cnc),
        'zero_install':sum(r[1]==0 for r in cnc),'zero_remove':sum(r[2]==0 for r in cnc)}
    result['workbook']=out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw',type=Path,default=Path(__file__).resolve().parents[1]/'data/raw')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.resolve().is_relative_to(args.raw.resolve()):
        p.error('Output must be outside raw source data')
    result={'files':{},'layers':{},'audit_environment':{
        'python':sys.version.split()[0],
        'packages':{name:importlib.metadata.version(name) for name in ('pyshp','pyproj','shapely','openpyxl')},
    }}
    for f in sorted(args.raw.iterdir()):
        if f.is_file():
            b=f.read_bytes()
            result['files'][f.name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob_sha1':git_blob(b)}
    layers=audit_layers(args.raw,result)
    audit_topology(args.raw,layers,result)
    audit_damage(layers,result)
    audit_workbook(args.raw,result)
    args.output.write_text(json.dumps(result,indent=2,default=str)+'\n')
    print('Aggregate report:',args.output)


if __name__=='__main__':
    main()

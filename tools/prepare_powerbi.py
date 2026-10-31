"""Create a fresh ignored local PBIP copy bound to the current immutable Gold build."""
from datetime import datetime, timezone
from pathlib import Path
import json
import re
import shutil
import uuid
import hashlib
from tools.build_powerbi_model import ROOT,PBI,literal


def restore_compatible_cache(folder):
    """Reuse only a local cache saved against exactly the same sources and model members."""
    model_name='BankingCustomerAnalytics.SemanticModel'
    target=folder/model_name
    def signature(model):
        expressions=(model/'definition/expressions.tmdl').read_text(encoding='utf-8-sig')
        paths=dict(re.findall(r'(?m)^expression (\w+DataPath) = "([^"]*)"',expressions))
        tables={p.name for p in (model/'definition/tables').glob('*.tmdl')}
        measures=set()
        for file in (model/'definition/tables').glob('*.tmdl'):
            for line in file.read_text(encoding='utf-8-sig').splitlines():
                if line.lstrip().startswith('measure '):
                    measures.add(line.strip().split(' =',1)[0])
        return paths,tables,measures
    wanted=signature(target)
    candidates=sorted((PBI/'.local').glob('*/'+model_name+'/.pbi/cache.abf'),key=lambda p:p.stat().st_mtime,reverse=True)
    for cache in candidates:
        source_model=cache.parents[1]
        if source_model==target:continue
        try:
            if signature(source_model)!=wanted:continue
        except (OSError,UnicodeError):
            continue
        destination=target/'.pbi/cache.abf';destination.parent.mkdir(exist_ok=True)
        shutil.copy2(cache,destination)
        return {'compatible_local_cache_restored':True,'cache_source':str(cache),'cache_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'cache_bytes':destination.stat().st_size,'cache_scope':'Previously saved local data; current Desktop visual acceptance still required'}
    return {'compatible_local_cache_restored':False,'cache_scope':'No compatible saved cache; Desktop Refresh then Save required'}


def prepare():
    manifest=json.loads((ROOT/'data/reports/latest_gold.json').read_text())
    folder=PBI/'.local'/('ready_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'_'+uuid.uuid4().hex[:6])
    folder.mkdir(parents=True,exist_ok=False)
    for item in ['BankingCustomerAnalytics.Report','BankingCustomerAnalytics.SemanticModel']:
        shutil.copytree(PBI/item,folder/item,ignore=shutil.ignore_patterns('.pbi'))
    shutil.copyfile(PBI/'BankingCustomerAnalytics.pbip',folder/'BankingCustomerAnalytics.pbip')
    path=folder/'BankingCustomerAnalytics.SemanticModel/definition/expressions.tmdl'
    text=path.read_text(encoding='utf-8')
    pattern=r'(?m)^expression GoldDataPath = "(?:[^"]|"")*" meta'
    text,count=re.subn(pattern,lambda _: 'expression GoldDataPath = '+literal(Path(manifest['powerbi_path']).as_posix())+' meta',text,count=1)
    if count!=1:raise ValueError('Expected GoldDataPath parameter not found.')
    synthetic_path=ROOT/'data/reports/latest_synthetic.json'
    synthetic=None
    if 'expression SyntheticGoldDataPath' in text:
        synthetic=json.loads(synthetic_path.read_text(encoding='utf-8'))
        if synthetic['original_gold_build_id']!=manifest['gold_build_id']:raise ValueError('Synthetic and original Gold builds are incompatible')
        text,count=re.subn(r'(?m)^expression SyntheticGoldDataPath = "(?:[^"]|"")*" meta',lambda _: 'expression SyntheticGoldDataPath = '+literal(Path(synthetic['powerbi_path']).as_posix())+' meta',text,count=1)
        if count!=1:raise ValueError('SyntheticGoldDataPath parameter not found')
    ml_path=ROOT/'data/reports/latest_ml.json';ml=None
    if 'expression MLGoldDataPath' in text:
        ml=json.loads(ml_path.read_text(encoding='utf-8'))
        if not synthetic or ml['synthetic_build_id']!=synthetic['synthetic_build_id']:raise ValueError('ML and synthetic builds are incompatible')
        text,count=re.subn(r'(?m)^expression MLGoldDataPath = "(?:[^"]|"")*" meta',lambda _: 'expression MLGoldDataPath = '+literal(Path(ml['powerbi_path']).as_posix())+' meta',text,count=1)
        if count!=1:raise ValueError('MLGoldDataPath parameter not found')
    analytics_path=ROOT/'data/reports/latest_analytics.json';analytics=None
    if 'expression AnalyticsGoldDataPath' in text:
        analytics=json.loads(analytics_path.read_text(encoding='utf-8'))
        if not ml or analytics['ml_build_id']!=ml['ml_build_id'] or analytics['synthetic_build_id']!=synthetic['synthetic_build_id']:raise ValueError('Analytics input versions are incompatible with the report')
        text,count=re.subn(r'(?m)^expression AnalyticsGoldDataPath = "(?:[^"]|"")*" meta',lambda _: 'expression AnalyticsGoldDataPath = '+literal(Path(analytics['powerbi_path']).as_posix())+' meta',text,count=1)
        if count!=1:raise ValueError('AnalyticsGoldDataPath parameter not found')
    path.write_text(text,encoding='utf-8')
    pointer={'local_pbip':str(folder/'BankingCustomerAnalytics.pbip'),'gold_build_id':manifest['gold_build_id'],'gold_data_path':manifest['powerbi_path'],'native_refresh_completed':False}
    if synthetic:pointer.update({'synthetic_build_id':synthetic['synthetic_build_id'],'synthetic_gold_data_path':synthetic['powerbi_path'],'data_origin':'Original snapshot + clearly labeled SYNTHETIC DEMO DATA'})
    if ml:pointer.update({'ml_build_id':ml['ml_build_id'],'ml_gold_data_path':ml['powerbi_path'],'ml_model_label':'SYNTHETIC DEMO MODEL'})
    if analytics:pointer.update({'analytics_build_id':analytics['analytics_build_id'],'analytics_gold_data_path':analytics['powerbi_path'],'analytics_label':'SYNTHETIC DEMO ANALYTICS'})
    pointer.update(restore_compatible_cache(folder))
    stable=PBI/'.local/BankingCustomerAnalytics.pbip'
    entry=json.loads((folder/'BankingCustomerAnalytics.pbip').read_text(encoding='utf-8'))
    entry['artifacts'][0]['report']['path']=folder.name+'/BankingCustomerAnalytics.Report'
    stable.write_text(json.dumps(entry,indent=2),encoding='utf-8')
    pointer['open_pbip']=str(stable)
    (PBI/'.local/latest.json').write_text(json.dumps(pointer,indent=2),encoding='utf-8')
    print(json.dumps(pointer,indent=2))
    return pointer


if __name__=='__main__':prepare()

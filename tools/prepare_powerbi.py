"""Create a fresh ignored local PBIP copy bound to the current immutable Gold build."""
from datetime import datetime, timezone
from pathlib import Path
import json
import re
import shutil
import uuid
from tools.build_powerbi_model import ROOT,PBI,literal


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
    path.write_text(text,encoding='utf-8')
    pointer={'local_pbip':str(folder/'BankingCustomerAnalytics.pbip'),'gold_build_id':manifest['gold_build_id'],'gold_data_path':manifest['powerbi_path'],'native_refresh_completed':False}
    (PBI/'.local/latest.json').write_text(json.dumps(pointer,indent=2),encoding='utf-8')
    print(json.dumps(pointer,indent=2))
    return pointer


if __name__=='__main__':prepare()

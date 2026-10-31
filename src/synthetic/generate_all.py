"""Run python -m src.synthetic.generate_all; generated sources contain linked sensitive IDs."""
import hashlib
import json
from pathlib import Path
from .common import ROOT, LABEL, context, settings
from . import generate_products, generate_payroll, generate_campaigns, generate_services, generate_digital_interactions, generate_satisfaction


def generate(customers,cfg):
    ctx=context(customers,cfg)
    products=generate_products.generate(ctx)
    payroll=generate_payroll.generate(ctx,products)
    campaigns=generate_campaigns.generate(ctx,products)
    services=generate_services.generate(ctx,campaigns)
    return {'products':products,'payroll':payroll,'campaigns':campaigns,
            'digital_interactions':generate_digital_interactions.generate(ctx,services),
            'value_added_services':services,'customer_satisfaction':generate_satisfaction.generate(ctx)}


def publish_sources(customers,cfg,folder=None):
    folder=Path(folder or ROOT/'data/raw_synthetic');folder.mkdir(parents=True,exist_ok=True)
    tables=generate(customers,cfg);hashes={}
    for name,table in tables.items():
        path=folder/(name+'.csv');table.to_csv(path,index=False,lineterminator='\n')
        hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    (folder/'manifest.json').write_text(json.dumps({'data_origin':LABEL,'seed':cfg['seed'],'config':cfg,'rows':{k:len(v) for k,v in tables.items()},'sha256':hashes},indent=2),encoding='utf-8')
    return tables,hashes


if __name__=='__main__':
    import pandas as pd
    manifest=json.loads((ROOT/'data/reports/latest_gold.json').read_text())
    customers=pd.read_parquet(Path(manifest['parquet_path'])/'dim_customer.parquet')
    tables,_=publish_sources(customers,settings())
    print(json.dumps({'data_origin':LABEL,'rows':{k:len(v) for k,v in tables.items()}},indent=2))

"""Validate PBIR schemas/references/layout and semantic-model metadata without Desktop."""
from pathlib import Path
import json
import re
from tools.powerbi_validation.schema_support import validate

ROOT=Path(__file__).resolve().parents[1]
PBI=ROOT/'powerbi'


def walk(value):
    if isinstance(value,dict):
        yield value
        for child in value.values():yield from walk(child)
    elif isinstance(value,list):
        for child in value:yield from walk(child)


def verify():
    source=json.loads((PBI/'model/model.source.json').read_text())['model']
    tables={table['name']:{col['name'] for col in table['columns']} for table in source['tables']}
    measures={m['name'] for table in source['tables'] for m in table.get('measures',[])}
    pages={p.parent.name:json.loads(p.read_text()) for p in (PBI/'BankingCustomerAnalytics.Report/definition/pages').glob('*/page.json')}
    paths=[PBI/'BankingCustomerAnalytics.pbip',PBI/'BankingCustomerAnalytics.Report/definition.pbir',PBI/'BankingCustomerAnalytics.SemanticModel/definition.pbism']+list((PBI/'BankingCustomerAnalytics.Report/definition').rglob('*.json'))
    errors=[];visual_count=0
    for path in paths:
        data=json.loads(path.read_text(encoding='utf-8'))
        try:validate(data)
        except Exception as error:errors.append(str(path.relative_to(PBI))+': '+str(error)[:1500])
        if path.name!='visual.json':continue
        visual_count+=1
        page=pages[path.parents[2].name]
        pos=data['position']
        if pos['x']<0 or pos['y']<0 or pos['x']+pos['width']>page['width']+1 or pos['y']+pos['height']>page['height']+1:errors.append(f'Out of bounds: {path}')
        for item in walk(data):
            for kind in ['Column','Measure']:
                if kind not in item:continue
                expression=item[kind]
                entity=expression.get('Expression',{}).get('SourceRef',{}).get('Entity')
                prop=expression.get('Property')
                if entity is None:continue
                if entity not in tables or prop not in (measures if kind=='Measure' else tables[entity]):errors.append(f'Invalid model reference {entity}.{prop}: {path}')
        for annotation in data.get('annotations',[]):
            if annotation['name']=='actionTarget' and annotation['value']!='reset_all' and annotation['value'] not in pages:errors.append('Invalid navigation target '+annotation['value'])
    # Overlap excludes no objects: authoring grid must keep all visible rectangles separate.
    overlaps=[]
    for name,page in pages.items():
        visuals=[json.loads(p.read_text()) for p in (PBI/'BankingCustomerAnalytics.Report/definition/pages'/name/'visuals').glob('*/visual.json')]
        names={v['name'] for v in visuals}
        for interaction in page.get('visualInteractions',[]):
            if interaction['source'] not in names or interaction['target'] not in names:errors.append('Invalid interaction reference '+name)
        for i,a in enumerate(visuals):
            for b in visuals[i+1:]:
                x,y=a['position'],b['position']
                if min(x['x']+x['width'],y['x']+y['width'])-max(x['x'],y['x'])>1 and min(x['y']+x['height'],y['y']+y['height'])-max(x['y'],y['y'])>1:overlaps.append(f'{name}: {a["name"]}/{b["name"]}')
    errors+=['Overlap: '+x for x in overlaps]
    report={'schema_files_checked':len(paths),'pages':len(pages),'visuals':visual_count,'tables':len(tables),'relationships':len(source['relationships']),'measures':len(measures),'errors':errors,'native_runtime_validated':False}
    output=PBI/'validation/project_validation.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    if errors:
        print('\n'.join(errors[:12]))
        raise ValueError(f'{len(errors)} project validation errors; see {output}')
    print(json.dumps(report,indent=2))
    return report


if __name__=='__main__':verify()

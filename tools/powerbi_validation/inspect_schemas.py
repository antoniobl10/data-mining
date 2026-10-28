import json
from .schema_support import get_schema

if __name__=='__main__':
    for name,version,defs in [('visualConfiguration','2.2.0',['VisualQuery','QueryState','Projection','VisualContainerObjects','VisualFormattingObjects','SyncGroup']),('page','2.0.0',['PageBinding','VisualInteraction','PageFormattingObjects']),('bookmark','1.0.0',['ExplorationState','SectionState','VisualState','FiltersState']),('report','2.0.0',['ThemeCollection','ResourcePackage'])]:
        s=get_schema(f'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/{name}/{version}/schema.json')
        print('\n',name,'DEFINITION NAMES',list(s.get('definitions',{})))
        for d in defs:
            if d in s.get('definitions',{}): print(d,json.dumps(s['definitions'][d])[:6000])

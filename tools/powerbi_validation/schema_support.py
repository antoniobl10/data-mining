"""Cache Microsoft's public PBIR schemas and validate authored textual artifacts."""
from pathlib import Path
import hashlib
import json
import urllib.request
from urllib.parse import urljoin
import jsonschema
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

ROOT=Path(__file__).resolve().parent
CACHE=ROOT/'schemas'


def get_schema(uri):
    uri=uri.split('#')[0]
    CACHE.mkdir(exist_ok=True)
    path=CACHE/(hashlib.sha256(uri.encode()).hexdigest()[:20]+'.json')
    if not path.exists():
        with urllib.request.urlopen(uri,timeout=30) as response: data=json.load(response)
        path.write_text(json.dumps(data,indent=2),encoding='utf-8')
        index_path=CACHE/'index.json'
        index=json.loads(index_path.read_text()) if index_path.exists() else {}
        index[uri]=path.name
        index_path.write_text(json.dumps(index,indent=2),encoding='utf-8')
    return json.loads(path.read_text(encoding='utf-8'))


def resource(uri):
    return Resource.from_contents(get_schema(uri),default_specification=DRAFT7)


def validate(document):
    schema=get_schema(document['$schema'])
    registry=Registry(retrieve=resource).with_resource(document['$schema'],Resource.from_contents(schema,default_specification=DRAFT7))
    jsonschema.Draft7Validator(schema,registry=registry).validate(document)


if __name__=='__main__':
    for name,version in [('visualContainer','2.4.0'),('visualConfiguration','2.2.0'),('page','2.0.0'),('report','2.0.0'),('pagesMetadata','1.0.0'),('bookmark','1.0.0'),('bookmarksMetadata','1.0.0'),('versionMetadata','1.0.0')]:
        url=f'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/{name}/{version}/schema.json'
        try:
            schema=get_schema(url)
            print(name,'required',schema.get('required'),'properties',list(schema.get('properties',{})))
        except Exception as error: print(name,type(error).__name__,str(error))

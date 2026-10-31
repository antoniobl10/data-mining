"""Append-only model versions; explicit Candidate/Champion/Archived lifecycle."""
import json
import joblib
from ..utils.config import path, write_json, digest


def register(cfg,task,version,model,metadata):
    root=path(cfg,'models'); registry_file=root/'registry.json'
    registry=json.loads(registry_file.read_text()) if registry_file.exists() else {'versions':[]}
    if any(r['task']==task and r['version']==version for r in registry['versions']):raise ValueError('Model version already exists')
    folder=root/task/version;folder.mkdir(parents=True,exist_ok=False)
    model_file=folder/'champion.joblib';joblib.dump(model,model_file)
    entry={**metadata,'task':task,'version':version,'status':'Candidate','model_path':str(model_file),'sha256':digest(model_file)}
    write_json(folder/'candidate.json',entry)
    for previous in registry['versions']:
        if previous['task']==task and previous['status']=='Champion':previous['status']='Archived'
    entry['status']='Champion';registry['versions'].append(entry)
    write_json(folder/'metadata.json',entry);write_json(registry_file,registry);return entry


def load(cfg,task):
    registry=json.loads((path(cfg,'models')/'registry.json').read_text())
    entries=[r for r in registry['versions'] if r['task']==task and r['status']=='Champion']
    if len(entries)!=1:raise ValueError('Expected one champion for '+task)
    entry=entries[0]
    if digest(entry['model_path'])!=entry['sha256']:raise ValueError('Model artifact checksum mismatch')
    # Controlled local artifacts only; never deserialize models received from untrusted sources.
    return joblib.load(entry['model_path']),entry

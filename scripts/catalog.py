"""Validate catalog DATA. Never import, evaluate, compile or run submitted scripts."""
import hashlib
import json
import re
from pathlib import Path

MAX_BYTES = 262144
FIELDS = {'schema','id','kind','name','summary','category','risk','version','scenario','files'}
FILES = {'manifest.json','actions.json','variables.json','keyboard.json','bubble.json','ui.json'}
ID = re.compile(r'[a-z0-9][a-z0-9_.-]{2,95}\Z')

def require(ok, message):
    if not ok:
        raise ValueError(message)

def unique_object(pairs):
    result = {}
    for key,value in pairs:
        require(key not in result, 'Duplicate JSON key')
        result[key]=value
    return result

def load(raw):
    require(isinstance(raw, bytes) and 2 <= len(raw) <= MAX_BYTES, 'JSON size')
    text=raw.decode('utf-8', errors='strict')
    depth=0; quoted=False; escaped=False
    for char in text:
        if quoted:
            if escaped: escaped=False
            elif char=='\\': escaped=True
            elif char=='"': quoted=False
        elif char=='"': quoted=True
        elif char in '[{':
            depth+=1
            require(depth<=32,'JSON depth')
        elif char in ']}':
            depth-=1
            require(depth>=0,'JSON nesting')
    require(not quoted and depth==0,'Incomplete JSON')
    return json.loads(text, object_pairs_hook=unique_object, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Non-finite number')))

def encoded(value):
    return (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')

def validate(package):
    require(type(package) is dict and set(package)==FIELDS,'Package fields')
    require(package['schema']=='qp1ng.marketplace.package.v1','Schema')
    require(type(package['id']) is str and ID.fullmatch(package['id']) and '..' not in package['id'],'ID')
    require(package['kind'] in ('scenario','tool'),'Kind')
    require(type(package['version']) is int and 1<=package['version']<=1000000,'Version')
    require(package['risk'] in ('LOW','MEDIUM','HIGH'),'Risk')
    for key,maximum in [('name',80),('summary',600),('category',60)]:
        value=package[key]
        require(type(value) is str and (key=='summary' or value) and len(value)<=maximum,'Label')
        require(all(ord(c)>=32 and not 127<=ord(c)<=159 and not 0x202a<=ord(c)<=0x202e and not 0x2066<=ord(c)<=0x2069 for c in value),'Label control character')
    if package['kind']=='scenario':
        s=package['scenario']
        require(type(s) is dict and package['files']=={},'Scenario body')
        require(s.get('id')==package['id'] and s.get('name')==package['name'],'Scenario identity')
        require(s.get('enabled') is False and s.get('runCount')==0 and s.get('lastRunAtMs') is None,'Scenario must be disabled')
        require(type(s.get('actions')) is list and 1<=len(s['actions'])<=64,'Action count')
        require(type(s.get('conditions')) is list and len(s['conditions'])<=32,'Condition count')
        require(type(s.get('trigger')) is dict and type(s['trigger'].get('type')) is str,'Trigger')
        for action in s['actions']:
            require(type(action) is dict and type(action.get('type')) is str,'Action')
            require(type(action.get('timeoutMs',30000)) is int and 1<=action.get('timeoutMs',30000)<=300000,'Action timeout')
    else:
        files=package['files']
        require(package['scenario'] is None and type(files) is dict and set(files)<=FILES and 'manifest.json' in files,'Tool files')
        require(all(type(v) is dict for v in files.values()),'Tool document')
        m=files['manifest.json']
        require(m.get('schema')=='qp1ng.tool.v1' and m.get('id')==package['id'] and m.get('name')==package['name'],'Manifest identity')
        policy=m.get('policy') or {}
        require(policy.get('risk',m.get('risk','LOW'))==package['risk'],'Manifest risk')
        require(policy.get('executionMode',m.get('executionMode','OFF')) in ('OFF','MANUAL_ONLY','ASK_EVERY_TIME'),'Execution mode')
        require(policy.get('networkDefault',False) is False,'Network default must be off')
        graph=files.get('actions.json',{})
        require(type(graph.get('nodes')) is list and 1<=len(graph['nodes'])<=128,'Flow nodes')
        ids=[n.get('id') for n in graph['nodes'] if type(n) is dict]
        require(len(ids)==len(graph['nodes']) and all(type(x) is str for x in ids) and len(set(ids))==len(ids),'Unique nodes')
    require(len(encoded(package))<=MAX_BYTES,'Encoded size')
    return package

def package_path(package):
    validate(package)
    return ('scenarios/' if package['kind']=='scenario' else 'tools/')+package['id']+'.json'

def build_index(root):
    root=Path(root)
    entries=[]
    for folder in ('scenarios','tools'):
        for path in sorted((root/folder).glob('*.json')):
            require(not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),'Package path')
            raw=path.read_bytes(); package=validate(load(raw))
            require(path.relative_to(root).as_posix()==package_path(package),'Filename mismatch')
            entry={k:package[k] for k in ('id','kind','name','summary','category','risk','version')}
            entry.update(path=package_path(package),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),minAppCode=172)
            entries.append(entry)
    require(len(entries)<=500,'Catalog count')
    result={'schema':'qp1ng.marketplace.index.v1','entries':sorted(entries,key=lambda e:(e['kind'],e['id']))}
    require(len(encoded(result))<=MAX_BYTES,'Catalog size')
    return result

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    index=encoded(build_index(root))
    if args.check:
        require((root/'index.json').read_bytes()==index,'Regenerate index.json with python scripts/catalog.py')
    else:
        (root/'index.json').write_bytes(index)
    print('Catalog validated:',len(load(index)['entries']),'packages')

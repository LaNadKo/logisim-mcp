"""Check archive integrity, allowlist membership, hashes and exclusion of private data."""
from pathlib import Path,PurePosixPath
import hashlib,json,re,sys,zipfile
def verify(path):
 with zipfile.ZipFile(path) as z:
  names=z.namelist();root=names[0].split('/')[0]
  manifest=json.loads(z.read(root+'/RELEASE-MANIFEST.json'))
  expected={root+'/'+e['path'] for e in manifest['files']}|{root+'/RELEASE-MANIFEST.json'}
  assert set(names)==expected and len(names)==len(expected),'Unexpected or duplicate archive entries'
  for e in manifest['files']:
   rel=e['path'];parts=PurePosixPath(rel).parts
   assert not PurePosixPath(rel).is_absolute() and '..' not in parts
   assert not any(p in parts for p in ['.state','.runtime','workspace','evidence','.git','__pycache__'])
   assert not any(p in parts for p in ['.connection.json','config.local.json'])
   digest=hashlib.sha256();size=0
   with z.open(root+'/'+rel) as f:
    while chunk:=f.read(1024*1024):digest.update(chunk);size+=len(chunk)
   assert digest.hexdigest()==e['sha256'] and size==e['bytes'],rel
   if Path(rel).suffix in ('.py','.md','.json','.java','.ps1','.cmd','.yml'):
    data=z.read(root+'/'+rel).lower()
    assert not re.search(rb'[a-z]:[\\/]+users[\\/]+[a-z0-9_]+',data),'Local author path: '+rel
  print(json.dumps({'verified':Path(path).name,'files':len(manifest['files']),'platforms':manifest['platforms']}))
if __name__=='__main__':verify(sys.argv[1])

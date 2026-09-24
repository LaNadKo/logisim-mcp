"""Build an allowlisted offline distribution, excluding all local state and user data."""
from pathlib import Path
import argparse,hashlib,json,sys,zipfile
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE))
from runtime import VERSION
ROOT_FILES=['AGENTS.md','AGENT_GUIDE.md','README.md','README.ru.md','README.en.md','LICENSE','THIRD_PARTY_NOTICES.md','SECURITY.md','CHANGELOG.md','CONTRIBUTING.md','config.example.json','dependencies.lock.json','build-info.json','runtime.py','windows_utf8.py','connect.py','launcher.py','mcp_server.py','server.py','workbench.py','build.py','index_manual.py','Workbench.java','LiveBridge.java','LogisimBridge.java','Attach.java','tools.json','manual-index.json','class-index.json','test_live.py','test_extended.py','test_agent_guidance.py','launch.cmd','launch.ps1','launch.sh','.gitignore','.gitattributes']
FOLDERS=['docs','licenses','scripts','tests','examples','.github']
def source_files():
 files=[BASE/n for n in ROOT_FILES]
 for folder in FOLDERS:
  files += [p for p in (BASE/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.log')]
 files += [BASE/'vendor/logisim-2.7.1.jar',BASE/'vendor/logisim-provenance.json',BASE/'lib/attach.jar',BASE/json.loads((BASE/'build-info.json').read_text())['jar'],BASE/'runtime-archives/SHA256SUMS']
 return sorted(set(files))
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--platform',default='universal');parser.add_argument('--output',type=Path,default=BASE/'dist');args=parser.parse_args()
 lock=json.loads((BASE/'dependencies.lock.json').read_text());keys=list(lock['platforms']) if args.platform=='universal' else [args.platform]
 entries=[e for key in keys for e in lock['platforms'][key].values()]+lock['sources']
 for e in entries:
  p=BASE/e['path']
  with p.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
  if digest!=e['sha256'] or p.stat().st_size!=e['size']:raise ValueError('Dependency verification failed: '+e['path'])
 files=source_files()+[BASE/e['path'] for e in entries]
 for p in files:
  if not p.is_file():raise FileNotFoundError(p)
  if not p.resolve().is_relative_to(BASE):raise ValueError('External path in release')
 args.output.mkdir(parents=True,exist_ok=True)
 target=args.output/f'logisim-mcp-{VERSION}-{args.platform}.zip';prefix=f'logisim-mcp-{VERSION}'
 manifest=[]
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
  for p in files:
   rel=p.relative_to(BASE).as_posix();info=zipfile.ZipInfo(prefix+'/'+rel);info.create_system=3
   info.external_attr=(0o100755 if p.suffix=='.sh' else 0o100644)<<16
   info.compress_type=zipfile.ZIP_STORED if p.suffix in ('.gz','.zip','.jar','.png') else zipfile.ZIP_DEFLATED
   digest=hashlib.sha256()
   with p.open('rb') as source,z.open(info,'w',force_zip64=True) as dest:
    while chunk:=source.read(1024*1024):digest.update(chunk);dest.write(chunk)
   manifest.append({'path':rel,'sha256':digest.hexdigest(),'bytes':p.stat().st_size})
  z.writestr(prefix+'/RELEASE-MANIFEST.json',json.dumps({'version':VERSION,'platforms':keys,'files':manifest},indent=2)+'\n')
 with target.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
 (args.output/(target.name+'.sha256')).write_text(digest+'  '+target.name+'\n',encoding='ascii')
 print(json.dumps({'archive':str(target),'bytes':target.stat().st_size,'sha256':digest,'files':len(files)}))
if __name__=='__main__':main()

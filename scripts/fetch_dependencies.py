"""Fetch pinned redistributable runtimes; never execute downloads or use latest URLs."""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,sys,urllib.request
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
from runtime import platform_key

def sha256(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def dependency_path(relative):
    relative=Path(relative)
    if relative.is_absolute() or relative.drive or '..' in relative.parts:
        raise ValueError('Lock path outside package: '+str(relative))
    path=(BASE/relative).resolve()
    # Windows can spell the same existing directory as a long path, an 8.3
    # alias or an extended-length path. Compare directory identity as well as
    # spelling, while still rejecting links that resolve outside the package.
    if not path.is_relative_to(BASE):
        if not any(parent.is_dir() and parent.samefile(BASE) for parent in path.parents):
            raise ValueError(f'Lock path outside package: {path} (root: {BASE})')
    return path

def fetch(entry,verify_only=False):
    path=dependency_path(entry['path'])
    if path.is_file() and path.stat().st_size==entry['size'] and sha256(path)==entry['sha256']:return entry['path']+' verified'
    if verify_only:raise ValueError('Missing or corrupt dependency: '+entry['path'])
    path.parent.mkdir(parents=True,exist_ok=True)
    partial=path.with_name(path.name+'.part')
    request=urllib.request.Request(entry['url'],headers={'User-Agent':'LaNadKo-logisim-mcp'})
    try:
        with urllib.request.urlopen(request,timeout=120) as response,partial.open('wb') as output:
            while block:=response.read(1024*1024):output.write(block)
        if partial.stat().st_size!=entry['size'] or sha256(partial)!=entry['sha256']:raise ValueError('Checksum mismatch: '+entry['path'])
        partial.replace(path)
    finally:partial.unlink(missing_ok=True)
    return entry['path']+' downloaded and verified'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all',action='store_true',help='Fetch all five platform runtimes')
    parser.add_argument('--platform',help='Fetch a specific platform instead of the current one')
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args();lock=json.loads((BASE/'dependencies.lock.json').read_text())
    keys=list(lock['platforms']) if args.all else [args.platform or platform_key()]
    entries=[entry for key in keys for entry in lock['platforms'][key].values()]+lock['sources']
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        for result in executor.map(lambda e:fetch(e,args.verify_only),entries):print(result,flush=True)
    sums=''.join(e['sha256']+' '+e['path']+'\n' for p in lock['platforms'].values() for e in p.values())
    (BASE/'runtime-archives').mkdir(exist_ok=True)
    (BASE/'runtime-archives/SHA256SUMS').write_text(sums,encoding='ascii',newline='\n')
if __name__=='__main__':main()

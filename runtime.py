"""Relocatable paths. No global installs or user-specific defaults."""
from pathlib import Path
import json, os, platform, shutil
BASE=Path(__file__).resolve().parent
VERSION='1.0.0'
def platform_key():
    system={'Windows':'windows','Linux':'linux','Darwin':'macos'}.get(platform.system())
    arch={'AMD64':'x64','x86_64':'x64','arm64':'arm64','aarch64':'arm64'}.get(platform.machine())
    key=f'{system}-{arch}'
    if key not in ('windows-x64','linux-x64','linux-arm64','macos-x64','macos-arm64'):raise RuntimeError(f'Unsupported platform: {platform.system()} {platform.machine()}')
    return key
def config():
    path=BASE/'config.local.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
def configured_path(env,key,default):
    value=os.environ.get(env) or config().get(key) or default
    path=Path(value).expanduser()
    return (BASE/path).resolve() if not path.is_absolute() else path.resolve()
def workspace():return configured_path('LOGISIM_MCP_WORKSPACE','workspace','workspace')
def state_dir():return configured_path('LOGISIM_MCP_STATE_DIR','state_dir','.state')
def connection_file():return state_dir()/'connection.json'
def logisim_jar():return configured_path('LOGISIM_MCP_LOGISIM','logisim','vendor/logisim-2.7.1.jar')
def java_executable(tool='java'):
    executable=tool+('.exe' if os.name=='nt' else '')
    override=os.environ.get('LOGISIM_MCP_JAVA_HOME') or config().get('java_home');homes=[]
    if override:
        p=Path(override).expanduser();homes.append(p if p.is_absolute() else BASE/p)
    root=BASE/'.runtime'/platform_key()/'java'
    homes += [root]+list(root.glob('*'))+list(root.glob('*/Contents/Home'))
    if os.environ.get('JAVA_HOME'):homes.append(Path(os.environ['JAVA_HOME']))
    for home in homes:
        p=home/'bin'/executable
        if p.is_file():
            p=p.resolve()
            if os.name=='nt' and p.is_relative_to(root.resolve()):
                from windows_utf8 import prepare
                return prepare(p)
            return str(p)
    found=shutil.which(tool)
    if found:return found
    raise RuntimeError(f'{tool} missing. Run the portable launcher or set LOGISIM_MCP_JAVA_HOME to a JDK 17+ directory.')
def build_info():
    data=json.loads((BASE/'build-info.json').read_text(encoding='utf-8'));jar=Path(data['jar'])
    data['jar']=str((BASE/jar).resolve()) if not jar.is_absolute() else str(jar)
    return data
def private_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700);temporary=path.with_name(path.name+'.tmp')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(data,f)
    temporary.replace(path)
def java_command(*arguments):return [java_executable(),'-Dfile.encoding=UTF-8',*map(str,arguments)]
def process_options():return {'creationflags':0x08000000} if os.name=='nt' else {}

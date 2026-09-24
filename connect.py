"""Connect to a managed or explicitly selected classic Logisim JVM."""
import json, os, secrets, socket, subprocess, time, urllib.request
from pathlib import Path
from runtime import BASE, build_info, connection_file, java_command, private_json, process_options, state_dir, workspace
def health(cfg):
    request=urllib.request.Request(f"http://127.0.0.1:{int(cfg['port'])}/health",data=b'',headers={'X-Logisim-Token':cfg['token']})
    with urllib.request.urlopen(request,timeout=3) as response:return json.loads(response.read())
def valid_connection(cfg):
    try:
        status=health(cfg)
        return status['build']==build_info()['build'] and Path(status['workspace']).resolve()==workspace()
    except (OSError,ValueError,KeyError):return False
def new_connection():
    workspace().mkdir(parents=True,exist_ok=True)
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    return {'port':port,'token':secrets.token_hex(32),'workspace':str(workspace())}
def await_connection(cfg,timeout=20):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if valid_connection(cfg):private_json(connection_file(),cfg);return
        time.sleep(.2)
    raise RuntimeError('Logisim agent did not become ready. See .state/logisim.log; existing windows were not closed.')
def candidates():
    run=subprocess.run(java_command('--add-modules','jdk.attach','-cp',BASE/'lib/attach.jar','Attach','--list'),capture_output=True,text=True,encoding='utf-8',timeout=15,**process_options())
    if run.returncode:raise RuntimeError('Cannot enumerate JVMs. Use the bundled JDK 17+ and run Logisim as the same OS user.')
    result=[]
    for line in run.stdout.splitlines():
        pid,sep,name=line.partition('\t')
        if sep and ('logisim' in name.lower() or 'com.cburch' in name.lower()) and 'Attach' not in name:result.append((pid,name))
    return result
def connect(pid=None):
    saved=connection_file()
    if pid is None and saved.exists():
        try:
            if valid_connection(json.loads(saved.read_text(encoding='utf-8'))):return 'Connected'
        except (OSError,ValueError):pass
    pid=pid or os.environ.get('LOGISIM_MCP_PID')
    if pid is None:
        matches=candidates()
        if len(matches)!=1:raise RuntimeError(f'Found {len(matches)} Logisim JVMs. Run launch start, or launch attach --pid PID to choose the intended instance.')
        pid=matches[0][0]
    if not str(pid).isdigit():raise ValueError('PID must be a positive integer')
    cfg=new_connection();cfg['pid']=int(pid)
    options=state_dir()/'agent-options.json';private_json(options,cfg)
    subprocess.run(java_command('--add-modules','jdk.attach','-cp',BASE/'lib/attach.jar','Attach',pid,build_info()['jar'],'@uri:'+options.as_uri()),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=25,**process_options())
    # Older JVM attach may report an error after success; authenticated health is authoritative.
    try:await_connection(cfg)
    finally:options.unlink(missing_ok=True)
    return f'Connected to Logisim PID {pid}'
if __name__=='__main__':print(connect())

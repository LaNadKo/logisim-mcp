"""Relocation and live acceptance using only runtimes from a clean package copy."""
from pathlib import Path
import json,os,shutil,signal,subprocess,sys,tempfile
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE));sys.path.insert(0,str(BASE/'scripts'))
from runtime import platform_key
from package_release import source_files

def main():
    sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
    key=platform_key();lock=json.loads((BASE/'dependencies.lock.json').read_text())
    destination=Path(tempfile.mkdtemp(prefix='Logisim portable '))/'Moved bundle Тест 漢字'
    for file in source_files()+[BASE/e['path'] for e in lock['platforms'][key].values()]:
        target=destination/file.relative_to(BASE);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,target)
    prefix=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(destination/'launch.ps1')] if os.name=='nt' else ['sh',str(destination/'launch.sh')]
    env=dict(os.environ)
    for name in list(env):
        if name.startswith('LOGISIM_MCP_') or name in ('JAVA_HOME','PYTHONHOME','PYTHONPATH'):env.pop(name,None)
    def run(args,capture=False):return subprocess.run(args,cwd=tempfile.gettempdir(),env=env,check=True,text=True,encoding='utf-8',capture_output=capture,timeout=180)
    run(prefix+['doctor']);run(prefix+['test']);run(prefix+['build'])
    config=json.loads(run(prefix+['config'],True).stdout)
    expected=destination/('launch.ps1' if os.name=='nt' else 'launch.sh')
    assert any(Path(arg).is_file() and Path(arg).samefile(expected) for arg in config['mcpServers']['logisim']['args']),config
    python=destination/'.runtime'/key/'python/python'/('python.exe' if os.name=='nt' else 'bin/python3')
    assert python.is_file()
    try:
        run(prefix+['start'])
        run([str(python),'-X','utf8',str(destination/'scripts/smoke_live.py')])
        run([str(python),'-X','utf8',str(destination/'test_agent_guidance.py'),'-v'])
        run([str(python),'-X','utf8',str(destination/'test_live.py')])
        run([str(python),'-X','utf8',str(destination/'test_extended.py')])
        # Verify explicit dynamic attach to the managed test JVM as a separate path.
        state=json.loads((destination/'.state/connection.json').read_text())
        run(prefix+['attach','--pid',str(state['pid'])]);run(prefix+['doctor'])
        print('PASS relocation, bundled runtimes, protocol, 77 core, 13 extended, 7 native smoke and explicit attach: '+key)
    finally:
        statefile=destination/'.state/connection.json'
        if statefile.exists():
            state=json.loads(statefile.read_text());pid=int(state['pid'])
            # This PID belongs to the fresh managed JVM launched in this private test folder.
            if os.name=='nt':subprocess.run(['taskkill','/PID',str(pid),'/T','/F'],capture_output=True)
            else:
                try:os.kill(pid,signal.SIGTERM)
                except ProcessLookupError:pass
    # Keep the isolated directory for diagnosis; no user-owned files are removed.
if __name__=='__main__':main()

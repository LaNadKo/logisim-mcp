"""User CLI; mcp subcommand keeps stdout exclusively for JSON-RPC."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import argparse,json,os,subprocess
from runtime import BASE,VERSION,build_info,connection_file,java_command,java_executable,logisim_jar,platform_key,private_json,process_options,state_dir,workspace

def start(file=None):
    from connect import new_connection,await_connection,valid_connection
    if connection_file().exists():
        try:
            if valid_connection(json.loads(connection_file().read_text())):
                if file:
                    from mcp_server import call
                    print(json.dumps(call('project_open',{'path':str(Path(file).resolve())}),ensure_ascii=False))
                else:print('Logisim is already connected.')
                return
        except (OSError,ValueError):pass
    cfg=new_connection();options=state_dir()/'agent-options.json';private_json(options,cfg)
    # JVM instrumentation on Windows decodes native agent options differently
    # from ordinary Java arguments. Keep the agent argument entirely ASCII.
    agent=Path(build_info()['jar']).relative_to(BASE).as_posix()
    command=java_command('-Dapple.laf.useScreenMenuBar=false','-javaagent:'+agent+'=@uri:'+options.as_uri(),'-jar',logisim_jar())
    if file:command.append(str(Path(file).resolve()))
    with (state_dir()/'logisim.log').open('ab') as log:
        process=subprocess.Popen(command,stdout=log,stderr=log,stdin=subprocess.DEVNULL,cwd=BASE,**process_options())
    cfg['pid']=process.pid
    try:await_connection(cfg,30)
    finally:options.unlink(missing_ok=True)
    print('Logisim started. Workspace: '+str(workspace()))

def doctor():
    from connect import valid_connection
    checks={}
    for name,path in [('logisim',logisim_jar()),('agent',Path(build_info()['jar'])),('attach',BASE/'lib/attach.jar')]:checks[name]=path.is_file()
    run=subprocess.run(java_command('--list-modules'),capture_output=True,text=True,timeout=15,**process_options())
    checks['java_modules']=run.returncode==0 and all(m in run.stdout for m in ['java.desktop@','jdk.httpserver@','jdk.attach@'])
    if not checks['java_modules']:print('Java diagnostic: '+(run.stderr or run.stdout).strip(),file=sys.stderr)
    active=False
    if connection_file().exists():
        try:active=valid_connection(json.loads(connection_file().read_text()))
        except (OSError,ValueError):pass
    print(json.dumps({'version':VERSION,'platform':platform_key(),'python':sys.version.split()[0],'java':java_executable(),'workspace':str(workspace()),'checks':checks,'connected':active},ensure_ascii=False,indent=2))
    return 0 if all(checks.values()) else 1

def print_config(kind):
    if os.name=='nt':command='powershell.exe';args=['-NoProfile','-ExecutionPolicy','Bypass','-File',str(BASE/'launch.ps1'),'mcp']
    else:command='/bin/sh';args=[str(BASE/'launch.sh'),'mcp']
    if kind=='codex':
        print('[mcp_servers.logisim]\ncommand = '+json.dumps(command)+'\nargs = '+json.dumps(args)+'\nstartup_timeout_sec = 120\ntool_timeout_sec = 120')
    else:print(json.dumps({'mcpServers':{'logisim':{'command':command,'args':args}}},ensure_ascii=False,indent=2))

def main():
    sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description='Portable Logisim Live MCP '+VERSION)
    sub=parser.add_subparsers(dest='action')
    p=sub.add_parser('start',help='Open the bundled Logisim with its agent');p.add_argument('file',nargs='?')
    p=sub.add_parser('attach',help='Attach to an existing Logisim JVM');p.add_argument('--pid',type=int)
    sub.add_parser('mcp',help='Run the MCP stdio server')
    sub.add_parser('doctor',help='Check local runtime and connection')
    sub.add_parser('build',help='Rebuild the Java agent and attach helper')
    sub.add_parser('test',help='Run portable unit/protocol tests')
    p=sub.add_parser('config',help='Print MCP configuration for this location');p.add_argument('--format',choices=['json','codex'],default='json')
    args=parser.parse_args()
    try:
        if args.action in (None,'start'):start(getattr(args,'file',None))
        elif args.action=='attach':
            from connect import connect
            print(connect(args.pid))
        elif args.action=='doctor':return doctor()
        elif args.action=='config':print_config(args.format)
        elif args.action=='build':
            from build import build
            build()
        elif args.action=='test':return subprocess.call([sys.executable,'-m','unittest','discover','-s',str(BASE/'tests'),'-v'],cwd=BASE)
        elif args.action=='mcp':
            from mcp_server import serve
            serve()
        return 0
    except Exception as error:
        print(f'Logisim MCP: {error}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())

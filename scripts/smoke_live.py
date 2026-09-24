"""End-to-end native test in an isolated new project; preserves existing projects."""
from pathlib import Path
import json,sys,time,urllib.request,urllib.error
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE))
from connect import connect
from mcp_server import call
from runtime import connection_file,workspace,platform_key

def main():
 connect();out=workspace()/('smoke-'+str(time.time_ns()));out.mkdir(parents=True)
 created=[];checks=[]
 def passed(name):checks.append(name);print('PASS '+name,flush=True)
 def invoke(tool_name,**args):return call(tool_name,{'project':project,**args})
 project=call('project_new',{'name':'MCP_Portable_Smoke'})['ref'];created.append(project)
 try:
  # Native AND truth table, exact ports, wire routing, save, reopen and export.
  invoke('circuit_edit',actions=[{'kind':'add','library':'Wiring','component':'Pin','x':100,'y':90,'attributes':{'label':'a','tristate':'false'}},{'kind':'add','library':'Wiring','component':'Pin','x':100,'y':110,'attributes':{'label':'b','tristate':'false'}},{'kind':'add','library':'Gates','component':'AND Gate','x':250,'y':100,'attributes':{'inputs':'2','size':'30'}},{'kind':'add','library':'Wiring','component':'Pin','x':350,'y':100,'attributes':{'label':'y','output':'true','facing':'west'}}])
  snap=invoke('circuit_snapshot');gate=next(c for c in snap['components'] if c['factory']=='AND Gate')
  ports=sorted([p for p in gate['ports'] if p['input']],key=lambda p:p['y'])
  invoke('circuit_edit',actions=[{'kind':'wire','points':[[100,90],[ports[0]['x'],ports[0]['y']]]},{'kind':'wire','points':[[100,110],[ports[1]['x'],ports[1]['y']]]},{'kind':'wire','points':[[250,100],[350,100]]}])
  def vectors(ref):
   for n in range(4):
    got=call('pins_read_write',{'project':ref,'values':{'a':n>>1,'b':n&1}})['y']['value']
    assert got['defined'] and got['unsigned']==int(n==3),(n,got)
  vectors(project);passed('native AND: 4/4 truth-table rows')
  path=out/'roundtrip.circ';invoke('project_save',path=str(path))
  reopened=call('project_open',{'path':str(path)})['ref']
  if reopened not in created:created.append(reopened)
  vectors(reopened);passed('saved circuit reopened: 4/4 rows')
  invoke('circuit_export',path=str(out/'roundtrip.png'),scale=1.5,show_state=True,printer_view=False)
  assert (out/'roundtrip.png').stat().st_size>100;passed('native PNG export')
  assert not invoke('circuit_snapshot')['width_conflicts'];passed('no width conflicts')
  cfg=json.loads(connection_file().read_text())
  try:urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{cfg['port']}/health",data=b''),timeout=3)
  except urllib.error.HTTPError as e:assert e.code==403
  else:raise AssertionError('Missing token accepted')
  passed('unauthenticated bridge request rejected')
  # Independent CLI process terminates through an explicit halt output.
  invoke('circuit_manage',action='add',name='Halt')
  invoke('circuit_edit',actions=[{'kind':'add','library':'Wiring','component':'Constant','x':100,'y':100,'attributes':{'value':'0x1'}},{'kind':'add','library':'Wiring','component':'Pin','x':300,'y':100,'attributes':{'label':'halt','output':'true','facing':'west'}},{'kind':'wire','points':[[100,100],[300,100]]}])
  invoke('circuit_manage',action='main',name='Halt');invoke('project_save',path=str(out/'halt.circ'))
  cli=call('cli_verify',{'path':str(out/'halt.circ'),'formats':['table','halt'],'timeout_seconds':15})
  assert cli['exit_code']==0 and not cli['timed_out'],cli;passed('bundled Java headless CLI')
  invoke('circuit_manage',action='add',name='Ticks')
  invoke('circuit_edit',actions=[{'kind':'add','library':'Wiring','component':'Clock','x':100,'y':100,'attributes':{}},{'kind':'add','library':'Wiring','component':'Pin','x':300,'y':100,'attributes':{'label':'y','output':'true','facing':'west'}},{'kind':'wire','points':[[100,100],[300,100]]}])
  previous=None
  for _ in range(10):
   invoke('simulation_ticks',count=1);value=invoke('pins_read_write')['y']['value']['unsigned']
   if previous is not None:assert value!=previous
   previous=value
  passed('ten deterministic native clock ticks')
  report={'platform':platform_key(),'passed':len(checks),'checks':checks}
  (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
 finally:
  for ref in reversed(created):
   try:call('project_close',{'project':ref,'discard_changes':True})
   except Exception as e:print('Could not close smoke project: '+str(e),file=sys.stderr)
if __name__=='__main__':main()

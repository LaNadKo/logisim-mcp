"""Integration tests against an isolated project in the real open Logisim JVM."""
from pathlib import Path
import json,time,sys,subprocess
from mcp_server import call,TOOLS
from runtime import workspace
BASE=Path(__file__).resolve().parent
OUT=workspace()/'evidence'/time.strftime('%Y%m%d-%H%M%S');OUT.mkdir(parents=True,exist_ok=True)
results=[]
def test(name,fn):
 try:
  detail=fn();results.append({'name':name,'pass':True,'detail':detail});print('PASS',name,flush=True);return detail
 except Exception as e:
  results.append({'name':name,'pass':False,'error':str(e)});print('FAIL',name,str(e),flush=True)
 finally:(OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
def check(cond,msg='assertion failed'):
 if not cond:raise AssertionError(msg)
def native_method(ref,name,args=[],parameters=None):
 d=call('api_describe',{'ref':ref,'filter':name});ms=[m for m in d['methods'] if m['name']==name and len(m['parameters'])==len(args) and (parameters is None or m['parameters']==parameters)]
 check(bool(ms),'absent '+name);return call('api_invoke',{'ref':ref,'method':ms[0]['id'],'args':args})
project=call('project_new',{'name':'MCP_Acceptance_'+OUT.name})['ref']
def run(tool_name,**args):return call(tool_name,{'project':project,**args})
test('isolated project',lambda:project)
catalog=run('catalog_full');(OUT/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
components=[(lib['name'],t['name']) for lib in catalog for t in lib['tools'] if t['component']]
test('catalog contains every native library',lambda:check(len(catalog)==7))
created={}
for index,(lib,name) in enumerate(components):
 def instantiate(lib=lib,name=name,index=index):
  result=run('circuit_edit',actions=[{'kind':'add','library':lib,'component':name,'x':200+(index%6)*400,'y':200+(index//6)*220,'attributes':{}}]);id=result['created'][0]['id'];created[(lib,name)]=id;details=run('component_inspect',id=id);check(details['factory']==name);return {'id':id,'ports':len(details['ports']),'attributes':len(details['attributes'])}
 test('instantiate '+lib+'/'+name,instantiate)
def memory(name):
 id=created[('Memory',name)];data=run('memory_read_write',id=id,action='read',start=0,count=4);vals=[0,1,17,255];check(data['width']>=8);run('memory_read_write',id=id,action='write',start=0,count=4,values=vals);check(run('memory_read_write',id=id,action='read',start=0,count=4)['values']==vals);return name+' 4 words round-trip'
test('ROM contents read/write',lambda:memory('ROM'))
test('RAM contents read/write',lambda:memory('RAM'))
test('native menu inventory',lambda:len(run('menu_inventory')))
test('native project options',lambda:run('project_options'))
test('scratch project save',lambda:run('project_save',path=str(OUT/'catalog.circ')))
def rejected_batch():
 run('circuit_manage',action='add',name='AtomicBatch')
 try:run('circuit_edit',actions=[{'kind':'add','library':'Wiring','component':'Pin','x':100,'y':100,'attributes':{'label':'a'}},{'kind':'wire','points':[[100,100],[150,130]]}])
 except Exception:pass
 else:raise AssertionError('Diagonal wire accepted')
 check(len(run('circuit_snapshot')['components'])==0,'Failed batch leaked component')
test('failed edit batch is atomic',rejected_batch)
def bus():
 run('circuit_edit',actions=[{'kind':'add','library':'Wiring','component':'Pin','x':100,'y':100,'attributes':{'label':'A','width':'8','tristate':'true'}},{'kind':'add','library':'Wiring','component':'Pin','x':300,'y':100,'attributes':{'label':'Y','width':'8','output':'true','facing':'west'}},{'kind':'wire','points':[[100,100],[300,100]]}])
 for n in [0,1,127,128,255]:check(run('pins_read_write',values={'A':n})['Y']['value']['unsigned']==n)
 check(run('pins_read_write',values={'A':'10x00001'})['Y']['value']['binary'].replace(' ','')=='10x00001')
 run('pins_read_write',values={'A':165});check(run('net_probe',x=100,y=100)['unsigned']==165)
 return '8-bit values and unknown propagation'
test('multibit bus',bus)
def move_duplicate_undo():
 roots=run('native_roots');before=len(run('circuit_snapshot')['components']);run('circuit_edit',actions=[{'kind':'duplicate','id':'Pin@100,100','x':100,'y':200}]);check(len(run('circuit_snapshot')['components'])==before+1);native_method(roots['project']['ref'],'undoAction');check(len(run('circuit_snapshot')['components'])==before)
test('duplicate and undo',move_duplicate_undo)
def expression_build(nand):
 name='NandGenerated' if nand else 'Generated'
 analyzer=run('analyzer_create',inputs=['a','b'],outputs=['y'])['ref'];run('analyzer_set_expression',analyzer=analyzer,output='y',expression='a b' if nand else 'a ^ b');run('analyzer_build',analyzer=analyzer,name=name,two_input=True,nand_only=nand)
 for n in range(4):check(run('pins_read_write',values={'a':n>>1,'b':n&1})['y']['value']['unsigned']==((n==3) if nand else ((n>>1)^(n&1))))
 return analyzer
analyzer=test('native XOR synthesis',lambda:expression_build(False))
test('native NAND-only synthesis',lambda:expression_build(True))
def table_build():
 an=run('analyzer_create',inputs=['a','b'],outputs=['z'])['ref'];run('analyzer_set_table',analyzer=an,columns={'z':['0','1','1','x']});sop=run('analyzer_minimize',analyzer=an,format='sop',apply=True);pos=run('analyzer_minimize',analyzer=an,format='pos');check(len(pos['rows'])==4);run('analyzer_build',analyzer=an,name='DontCare');return {'sop':sop['expressions'],'pos':pos['expressions']}
test('truth-table dont-care SOP POS synthesis',table_build)
test('capture truth table from generated circuit',lambda:run('analyzer_capture'))
def export():
 data=run('circuit_export',path=str(OUT/'generated.png'),scale=2,show_state=True);check(Path(data['path']).stat().st_size>500);return data
test('native image export',export)
def api_appearance():
 roots=run('native_roots');desc=call('api_describe',{'class':'com.cburch.draw.shapes.Rectangle'});ctor=[x for x in desc['constructors'] if x['parameters']==['int']*4][0];shape=call('api_construct',{'method':ctor['id'],'args':[50,50,80,40]});app=roots['appearance']['ref'];native_method(app,'addObjects',[0,[shape]],['int','java.util.Collection']);objects=native_method(app,'getObjectsFromBottom');items=call('api_items',{'ref':objects['ref']});check(any(x.get('ref')==shape['ref'] for x in items['items']));return {'appearance_objects':items['total']}
test('native appearance editing via API',api_appearance)
def subcircuit():
 run('circuit_manage',action='add',name='Hierarchy');sub=run('circuit_edit',actions=[{'kind':'add','library':'project','component':'Generated','x':300,'y':200,'attributes':{}}])['created'][0];run('simulation_substate',action='enter',id=sub['id']);check(run('circuit_snapshot')['circuit']=='Generated');run('simulation_substate',action='parent');check(run('circuit_snapshot')['circuit']=='Hierarchy')
test('subcircuit instance state traversal',subcircuit)
def logger():
 run('circuit_manage',action='select',name='Generated');snapshot=run('circuit_snapshot');pins=[c['ref'] for c in snapshot['components'] if c['factory']=='Pin'];log=run('log_create')['ref'];run('log_select',log=log,components=pins);run('pins_read_write',values={'a':1,'b':0});samples=run('log_sample',log=log);check(len(samples)==3);return samples
test('native signal logging',logger)
test('final scratch save',lambda:run('project_save',path=str(OUT/'acceptance.circ')))
def stdio():
 requests=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'test','version':'1'}}},{'jsonrpc':'2.0','method':'notifications/initialized'},{'jsonrpc':'2.0','id':2,'method':'tools/list'},{'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'projects','arguments':{}}},{'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'circuit_edit','arguments':{'project':project,'actions':'invalid'}}},{'jsonrpc':'2.0','id':5,'method':'resources/list'}]
 proc=subprocess.run([sys.executable,str(BASE/'mcp_server.py')],input='\n'.join(json.dumps(r) for r in requests)+'\n',text=True,encoding='utf-8',capture_output=True,timeout=30);check(proc.returncode==0,proc.stderr);responses=[json.loads(l) for l in proc.stdout.splitlines()];check(len(responses)==5);check(len(responses[1]['result']['tools'])==len(TOOLS));check(responses[3]['result']['isError']);check(len(responses[4]['result']['resources'])==131);return {'tools':len(TOOLS),'resources':131,'invalid_argument_rejected':True}
test('MCP stdio lifecycle tools resources and schema validation',stdio)
(BASE/'latest-evidence.json').write_text(json.dumps({'directory':str(OUT),'passed':sum(r['pass'] for r in results),'total':len(results)},indent=2),encoding='utf-8')
print('RESULT',sum(r['pass'] for r in results),'/',len(results),'EVIDENCE',OUT)
sys.exit(0 if all(r['pass'] for r in results) else 1)

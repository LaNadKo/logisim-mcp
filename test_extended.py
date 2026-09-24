from pathlib import Path
import json,sys,time
from mcp_server import call
from runtime import workspace
BASE=Path(__file__).resolve().parent;OUT=workspace()/'evidence'/('extended-'+time.strftime('%Y%m%d-%H%M%S'));OUT.mkdir(parents=True)
results=[]
def test(name,fn):
 try:r=fn();results.append({'name':name,'pass':True,'detail':r});print('PASS',name,flush=True);return r
 except Exception as e:results.append({'name':name,'pass':False,'error':str(e)});print('FAIL',name,str(e),flush=True)
 finally:(OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
def check(ok,msg='assertion failed'):
 if not ok:raise AssertionError(msg)
project=call('project_new',{'name':'MCP_Extended_'+OUT.name})['ref']
def run(tool,**args):return call(tool,{'project':project,**args})
def native(ref,name,args=[],parameters=None):
 methods=call('api_describe',{'ref':ref,'filter':name})['methods'];m=[m for m in methods if m['name']==name and len(m['parameters'])==len(args) and (parameters is None or m['parameters']==parameters)];check(bool(m),'Missing '+name);return call('api_invoke',{'ref':ref,'method':m[0]['id'],'args':args})
def add(lib,name,x,y,**attrs):return run('circuit_edit',actions=[{'kind':'add','library':lib,'component':name,'x':x,'y':y,'attributes':{k:str(v) for k,v in attrs.items()}}])['created'][0]
ram=add('Memory','RAM',400,200)
def hex_roundtrip():
 run('memory_read_write',id=ram['id'],action='write',start=0,count=4,values=[1,2,254,255]);run('memory_export_hex',id=ram['id'],path=str(OUT/'ram.hex'),count=4);run('memory_read_write',id=ram['id'],action='write',start=0,count=4,values=[0]*4);run('memory_import_hex',id=ram['id'],path=str(OUT/'ram.hex'));check(run('memory_read_write',id=ram['id'],action='read',count=4)['values']==[1,2,254,255]);(OUT/'rle.hex').write_text('v2.0 raw\n3*ab ff\n');run('memory_import_hex',id=ram['id'],path=str(OUT/'rle.hex'));check(run('memory_read_write',id=ram['id'],action='read',count=4)['values']==[171,171,171,255]);return 'plain and RLE'
test('native hex import/export roundtrip',hex_roundtrip)
test('statistics native counts',lambda:run('circuit_statistics'))
test('read all native preferences',lambda:len(run('application_preferences')))
test('read actual Swing windows',lambda:len(call('native_windows',{'depth':2})))
def selection():
 pin=add('Wiring','Pin',100,100,label='a');run('selection_edit',action='select',components=[pin['id']]);check(len(run('selection_edit',action='read'))==1);run('selection_edit',action='copy');run('selection_edit',action='paste');run('selection_edit',action='move',dx=0,dy=100);run('selection_edit',action='drop');snap=run('circuit_snapshot');check(sum(c['factory']=='Pin' for c in snap['components'])==2);return 'copy/paste/move/drop'
test('native clipboard and selection',selection)
def circuit_management():
 run('circuit_manage',action='add',name='Temporary');run('circuit_manage',action='main',name='Temporary');run('circuit_manage',action='move',name='Temporary',index=0);check(run('circuit_manage',action='list')[0]['name']=='Temporary');run('circuit_manage',action='main',name='main');run('circuit_manage',action='remove',name='Temporary');check(len(run('circuit_manage',action='list'))==1)
test('circuit add reorder main remove',circuit_management)
def shapes():
 run('circuit_manage',action='add',name='Appearance');app=run('native_roots')['appearance']['ref'];created=[]
 for classname,args,types in [('Rectangle',[40,40,80,40],['int']*4),('Oval',[40,120,80,40],['int']*4),('RoundRectangle',[40,200,80,40],['int']*4),('Line',[40,280,120,280],['int']*4),('Text',[40,320,'MCP'],['int','int','java.lang.String'])]:
  d=call('api_describe',{'class':'com.cburch.draw.shapes.'+classname});ctors=[c for c in d['constructors'] if c['parameters']==types];check(bool(ctors),classname+' constructor '+str(d['constructors']));shape=call('api_construct',{'method':ctors[0]['id'],'args':args});native(app,'addObjects',[0,[shape]],['int','java.util.Collection']);created.append(shape)
 native(app,'translateObjects',[[created[0]],10,10],['java.util.Collection','int','int']);native(app,'removeObjects',[[created[0]]],['java.util.Collection']);return {'shapes':len(created),'moved_removed':1}
test('native appearance shape family',shapes)
def clock_ticks():
 run('circuit_manage',action='add',name='ClockCheck');clock=add('Wiring','Clock',100,100);output=add('Wiring','Pin',300,100,label='Y',output='true',facing='west');run('circuit_edit',actions=[{'kind':'wire','points':[[100,100],[300,100]]}]);run('simulation_ticks',count=1);a=run('pins_read_write')['Y']['value']['unsigned'];run('simulation_ticks',count=1);b=run('pins_read_write')['Y']['value']['unsigned'];check(a!=b);return [a,b]
test('deterministic live clock ticks',clock_ticks)
def logging_file():
 run('circuit_manage',action='add',name='LogCheck');a=add('Wiring','Pin',100,100,label='a',tristate='false');y=add('Wiring','Pin',300,100,label='y',output='true',facing='west');run('circuit_edit',actions=[{'kind':'wire','points':[[100,100],[300,100]]}]);log=run('log_create')['ref'];run('log_select',log=log,components=[a['id'],y['id']]);run('log_file',log=log,path=str(OUT/'signals.tsv'),enabled=True,header=True)
 for v in [0,1,0]:run('pins_read_write',values={'a':v});run('log_sample',log=log)
 time.sleep(0.8);run('log_file',log=log,enabled=False);check((OUT/'signals.tsv').exists());text=(OUT/'signals.tsv').read_text();check('1' in text and '0' in text,text);return text
test('native logger writes signal transitions',logging_file)
def library():
 path=OUT/'library.circ';run('project_save',path=str(path));other=call('project_new',{'name':'MCP_LibraryConsumer'})['ref'];loaded=call('library_manage',{'project':other,'action':'load','path':str(path)});cat=call('catalog_full',{'project':other});name=[c['name'] for c in cat if c['ref']==loaded['ref']][0];call('library_manage',{'project':other,'action':'reload','name':name});call('library_manage',{'project':other,'action':'unload','name':name});return name
test('external circuit library load reload unload',library)
def field_access():
 roots=run('native_roots');desc=call('api_describe',{'class':'com.cburch.logisim.data.Direction'});east=[f for f in desc['fields'] if f['name']=='EAST'][0];value=call('api_field',{'field':east['id']});check(value['class']=='com.cburch.logisim.data.Direction');return value['class']
test('native constant field access',field_access)
def paths():
 try:run('project_save',path=str(BASE.parent.parent/'outside.circ'))
 except Exception:pass
 else:raise AssertionError('outside path allowed')
 try:run('memory_read_write',id='not-present',action='read',count=10)
 except Exception:pass
 else:raise AssertionError('missing memory allowed')
test('invalid targets rejected',paths)
def introspection():
 classes=json.loads((BASE/'class-index.json').read_text());inventory=[];failed=[]
 with (OUT/'native-api.jsonl').open('w',encoding='utf-8') as f:
  for name in classes:
   try:d=call('api_describe',{'class':name});f.write(json.dumps(d,ensure_ascii=False)+'\n');inventory.append({'class':name,'methods':len(d['methods']),'fields':len(d['fields']),'constructors':len(d['constructors'])})
   except Exception as e:failed.append({'class':name,'error':str(e)})
 (OUT/'api-summary.json').write_text(json.dumps({'classes':inventory,'failed':failed},ensure_ascii=False,indent=2),encoding='utf-8');check(all(f['class']=='com.cburch.logisim.gui.start.MacOsAdapter' and 'com.apple.eawt.ApplicationAdapter' in f['error'] for f in failed),str(failed));return {'classes':len(inventory),'platform_exclusions':failed,'methods_including_inherited':sum(c['methods'] for c in inventory),'fields_including_inherited':sum(c['fields'] for c in inventory)}
test('discover entire packaged native API',introspection)
print('RESULT',sum(r['pass'] for r in results),'/',len(results),'EVIDENCE',OUT)
(BASE/'extended-evidence.json').write_text(json.dumps({'directory':str(OUT),'passed':sum(r['pass'] for r in results),'total':len(results)},indent=2),encoding='utf-8')
sys.exit(0 if all(r['pass'] for r in results) else 1)

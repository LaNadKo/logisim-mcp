import json,urllib.request,urllib.error,subprocess
from zipfile import ZipFile
from pathlib import Path
from runtime import connection_file,java_command,logisim_jar,workspace,process_options
BASE=Path(__file__).resolve().parent
S={'type':'string'}; N={'type':'number'}; I={'type':'integer'}; B={'type':'boolean'}; O={'type':'object'}
STRINGS={'type':'array','items':S}; ANYS={'type':'array','items':{}}
TOOLS=[]; OPS={}
def tool(name,op,desc,props=None,required=None,project=True,read=False):
 props=dict(props or {})
 if project:props={'project':S,**props}
 req=list(props) if required is None else (['project'] if project else [])+required
 TOOLS.append({'name':name,'description':desc,'inputSchema':{'type':'object','properties':props,'required':req,'additionalProperties':False},'annotations':{'readOnlyHint':read,'destructiveHint':not read,'openWorldHint':False}});OPS[name]=op
tool('projects','projects','List live projects with unambiguous session refs',project=False,read=True)
tool('project_new','new_project','Create a new live project using the current template',{'name':S},project=False)
tool('project_open','open','Open a workspace .circ project without replacing existing projects',{'path':S},project=False)
tool('project_close','close','Close a live project window. Refuses unsaved changes unless discard_changes=true; refuses the last project to avoid exiting the runtime.',{'discard_changes':B},required=[])
tool('native_roots','roots','Get typed refs to project, circuit, simulator, appearance, options and canvas',read=True)
tool('catalog_full','catalog','Every loaded component and editor tool, all native default attributes and handles',read=True)
tool('circuit_snapshot','snapshot','Read components, exact ports, net values, wires and width conflicts',read=True)
tool('component_inspect','component','Inspect one component by stable session ref or Factory@x,y id',{'id':S},read=True)
tool('circuit_edit','edit','One undoable batch: add component; wire points; remove_wire exact from/to; remove; attribute key/value; move/duplicate x/y. Validate whole batch before applying. Move does not reroute wires.',{'actions':{'type':'array','minItems':1,'maxItems':1000,'items':{'type':'object','properties':{'kind':{'type':'string','enum':['add','wire','remove_wire','remove','attribute','move','duplicate']},'library':S,'component':S,'x':I,'y':I,'attributes':{'type':'object','additionalProperties':S},'points':{'type':'array','items':{'type':'array','items':I,'minItems':2,'maxItems':2}},'from':{'type':'array','items':I,'minItems':2,'maxItems':2},'to':{'type':'array','items':I,'minItems':2,'maxItems':2},'id':S,'key':S,'value':S},'required':['kind'],'additionalProperties':False}}})
tool('pins_read_write','pins','Read all pins, or set input values (unsigned integer or exact-width 01xE string). Supports 1..32 bits; propagates and repaints.',{'values':{'type':'object','additionalProperties':{'anyOf':[I,S]}}},required=[])
tool('net_probe','probe','Read simulated value at a wire/port coordinate',{'x':I,'y':I},read=True)
tool('circuit_manage','circuit','List/add/select/remove/reorder/set-main circuit or set circuit attribute. Removal refuses used/last circuit.',{'action':{'type':'string','enum':['list','add','select','remove','move','main','attribute']},'name':S,'index':I,'key':S,'value':S},required=['action'])
tool('project_save','save','Save workspace .circ. Existing destination requires overwrite=true and is backed up first.',{'path':S,'overwrite':B},required=['path'])
tool('analyzer_create','analyzer_new','Create native combinational analyzer, up to 8 one-bit inputs and outputs',{'inputs':STRINGS,'outputs':STRINGS})
tool('analyzer_capture','analyzer_from_circuit','Derive truth table and expressions from current combinational circuit; unsuitable for sequential circuits',{'derive_expression':B},required=[])
tool('analyzer_set_expression','analyzer_expression','Parse native Boolean syntax for one output (AND, OR, XOR, NOT or symbolic equivalents)',{'analyzer':S,'output':S,'expression':S})
tool('analyzer_set_table','analyzer_table','Set complete output truth-table columns, row order binary ascending; accepts 0,1,x',{'analyzer':S,'columns':{'type':'object','additionalProperties':{'type':'array','items':{'type':'string','enum':['0','1','x']}}}})
tool('analyzer_minimize','analyzer_minimize','Native SOP/POS minimization with optional application to output expressions. Use when requested or required by the assignment; do not infer permission for a compact implementation. Follow logisim://guidance/agents.',{'analyzer':S,'format':{'type':'string','enum':['sop','pos']},'apply':B},required=['analyzer','format'])
tool('analyzer_read','analyzer_read','Read analyzer expressions, minimized forms and full truth table',{'analyzer':S},read=True)
tool('analyzer_build','analyzer_build','Native automatic circuit generation into a new circuit; optional two-input and NAND-only gates. Preserve the requested full structure and basis; no unrequested compact alternative. Check generated structure against the assignment. Follow logisim://guidance/agents. NAND-only cannot directly synthesize XOR expressions.',{'analyzer':S,'name':S,'two_input':B,'nand_only':B},required=['analyzer','name'])
tool('memory_read_write','memory','Read/write RAM state or ROM contents, 0-based addresses, unsigned words. Runtime RAM values are not stored in .circ; use export. ROM writes change project.',{'id':S,'action':{'type':'string','enum':['read','write']},'start':I,'count':{'type':'integer','minimum':0,'maximum':65536},'values':{'type':'array','maxItems':65536,'items':{'type':'integer','minimum':0,'maximum':4294967295}}},required=['id','action'])
tool('circuit_export','export','Export native circuit drawing to PNG/GIF/JPEG; state colors, printer view and scale options',{'path':S,'format':{'type':'string','enum':['png','gif','jpg']},'scale':{'type':'number','exclusiveMinimum':0,'maximum':8},'show_state':B,'printer_view':B,'overwrite':B},required=['path'])
tool('project_options','options','Read all native simulation options or set one native attribute',{'key':S,'value':S},required=[])
tool('library_manage','library','Load .circ or JAR library from workspace, reload loaded library, or unload unused library. JAR class_name is required for extension libraries.',{'action':{'type':'string','enum':['load','reload','unload']},'path':S,'name':S,'class_name':S},required=['action'])
tool('simulation_substate','substate','Enter live subcircuit instance state or return to parent simulation state',{'action':{'type':'string','enum':['enter','parent']},'id':S},required=['action'])
tool('menu_inventory','menu_list','Enumerate complete actual native application menu tree, enabled state and item handles',read=True)
tool('menu_action','menu_invoke','Queue a previously discovered native menu action. Can open modal UI, print, save or close; observe completion separately. Does not imply external submission approval.',{'item':S})
tool('log_create','log_create','Create native signal logging model for the current simulation state')
tool('log_select','log_select','Add components to native logger; RAM accepts address option. Discover supported logging types in manual.',{'log':S,'components':STRINGS,'option':I},required=['log','components'])
tool('log_sample','log_sample','Sample native selected log signals after propagation',{'log':S})
tool('log_file','log_file','Configure native logger output file/header/enabled; new workspace path only. Uses the active application logging model for continuous transitions.',{'log':S,'path':S,'header':B,'enabled':B},required=['log','enabled'])
tool('api_describe','api_describe','Discover constructors, methods and fields for a native com.cburch class or handle, including package-private APIs. Filter methods by substring. Discovery does not prove behavioral coverage.',{'class':S,'ref':S,'filter':S},required=[],project=False,read=True)
tool('api_invoke','api_call','Invoke an EXACT signature previously discovered by api_describe. Args: primitive, arrays/lists, workspace File path or {ref:handle}. Mutations may bypass undo; inspect documentation first.',{'method':S,'ref':S,'args':ANYS},required=['method'],project=False)
tool('api_construct','api_construct','Construct a native object using exact discovered constructor signature; object returned as session ref',{'method':S,'args':ANYS},required=['method'],project=False)
tool('api_field','api_field','Read exact previously discovered native field, returning primitive or object ref',{'field':S,'ref':S},required=['field'],project=False,read=True)
tool('api_items','api_items','Paginate arrays, lists, sets or maps returned by native methods',{'ref':S,'offset':I,'limit':{'type':'integer','minimum':1,'maximum':1000}},required=['ref'],project=False,read=True)
tool('api_release','api_release','Release session object refs no longer needed',{'refs':STRINGS},project=False)
tool('api_field_set','api_field_set','Set a previously discovered non-final native field. Advanced escape hatch; may bypass undo and propagation. Use typed tools when available.',{'field':S,'ref':S,'value':{}},required=['field','value'],project=False)
tool('native_windows','windows','Read Swing window/dialog trees for this Logisim JVM, including actual controls and handles',{'depth':{'type':'integer','minimum':0,'maximum':20}},required=[],project=False,read=True)
tool('native_widget','widget','Operate a discovered native Logisim widget: click button, set text, select combo/tab/list, set spinner, front window. Click is queued; observe results with native_windows.',{'ref':S,'action':{'type':'string','enum':['click','text','select','spinner','front']},'value':{},'index':I},required=['ref','action'],project=False)
tool('simulation_ticks','ticks','Synchronously execute a fixed number of clock ticks and settle after each; automatic ticking must be disabled',{'count':{'type':'integer','minimum':0,'maximum':10000}},required=[])
tool('simulation_control','simulate','Native simulation status/run/pause, tick, step, reset, automatic ticking and frequency. step/reset are asynchronous; poll status or propagate before dependent reads.',{'action':{'type':'string','enum':['status','propagate','tick','step','reset','run','pause','ticks_on','ticks_off','frequency']},'hz':{'type':'number','exclusiveMinimum':0,'maximum':4096}},required=['action'])
tool('circuit_undo','undo','Undo the latest file-affecting project action; simulated values are not undoable')
tool('circuit_statistics','statistics','Read native simple, unique and recursive component statistics',read=True)
tool('selection_edit','selection','Native selection and clipboard: select components, copy/cut/paste/drop/duplicate/delete/move, or read. Paste remains floating until move/drop.',{'action':{'type':'string','enum':['read','select','copy','cut','paste','drop','duplicate','delete','move']},'components':STRINGS,'dx':I,'dy':I},required=['action'])
tool('application_preferences','preferences','Read all native preference monitors or set one exact key with its correct value type; settings persist in Logisim',{'key':S,'value':{}},required=[])
tool('memory_export_hex','local_mem_export','Export RAM/ROM range as native v2.0 raw hexadecimal file; does not overwrite',{'id':S,'path':S,'start':I,'count':{'type':'integer','minimum':1,'maximum':65536}},required=['id','path','count'])
tool('memory_import_hex','local_mem_import','Load native v2.0 raw hex data (including count*word runs) into RAM/ROM; validate full file first',{'id':S,'path':S,'start':I},required=['id','path'])
tool('api_classes','local_classes','Search all 610 packaged top-level com.cburch classes for API discovery',{'query':S,'offset':I,'limit':I},required=[],project=False,read=True)
tool('manual_search','local_search','Search all 129 bundled English manual pages, including all libraries and menus',{'query':S,'limit':I},required=['query'],project=False,read=True)
tool('manual_read','local_read','Read one exact bundled manual page returned by manual_search',{'path':S},project=False,read=True)
tool('source_search','local_source_search','Search actual Java source bundled in this exact Logisim executable; returns source paths and matching line numbers',{'query':S,'path_contains':S,'limit':{'type':'integer','minimum':1,'maximum':100}},required=['query'],project=False,read=True)
tool('source_read','local_source_read','Read a bounded line range from a bundled Java source path returned by source_search',{'path':S,'start':{'type':'integer','minimum':1},'count':{'type':'integer','minimum':1,'maximum':500}},required=['path'],project=False,read=True)
tool('cli_verify','local_cli','Run classic Logisim headless verification with bounded timeout. Supports table/halt/speed/stats/tty, RAM -load, library -sub and keyboard stdin. Needs a self-terminating harness with halt output for normal completion.',{'path':S,'formats':{'type':'array','minItems':1,'items':{'type':'string','enum':['table','halt','speed','stats','tty']}},'load_image':S,'substitutions':{'type':'array','items':{'type':'object','properties':{'from':S,'to':S},'required':['from','to'],'additionalProperties':False}},'stdin':S,'timeout_seconds':{'type':'integer','minimum':1,'maximum':30}},required=['path'],project=False)
def rpc(op,**args):
 cfg=json.loads(connection_file().read_text(encoding='utf-8-sig'))
 data=json.dumps({'op':op,**args},ensure_ascii=False).encode('utf-8')
 request=urllib.request.Request(f"http://127.0.0.1:{cfg['port']}/v3",data=data,headers={'X-Logisim-Token':cfg['token'],'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(request,timeout=60) as response:return json.loads(response.read())
 except urllib.error.HTTPError as e:raise RuntimeError(e.read().decode()) from None
def call(name,args):
 op=OPS[name]
 if op=='edit':
  kinds={a['kind'] for a in args['actions']}
  if 'attribute' in kinds and len(kinds)>1:
   raise ValueError('Logisim 2.7.1 cannot safely mix attribute changes and structural edits in one transaction. Submit attributes in a separate circuit_edit call before rereading and moving components.')
 if op=='local_cli':
  def local(p):
   path=Path(p).resolve()
   if not path.is_relative_to(workspace()) or not path.is_file():raise ValueError('Expected existing workspace file')
   return str(path)
  command=java_command('-Djava.awt.headless=true','-jar',logisim_jar(),local(args['path']),'-tty',','.join(args.get('formats',['table','halt'])),'-locale','en')
  if 'load_image' in args:command+=['-load',local(args['load_image'])]
  for pair in args.get('substitutions',[]):command+=['-sub',local(pair['from']),local(pair['to'])]
  try:
   p=subprocess.run(command,input=args.get('stdin',''),text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=args.get('timeout_seconds',10));return {'exit_code':p.returncode,'stdout':p.stdout[:200000],'stderr':p.stderr[:20000],'timed_out':False}
  except subprocess.TimeoutExpired as e:return {'exit_code':None,'timed_out':True,'stdout':(e.stdout or b'')[:200000].decode('utf-8',errors='replace'),'stderr':(e.stderr or b'')[:20000].decode('utf-8',errors='replace')}
 if op in ('local_source_search','local_source_read'):
  with ZipFile(logisim_jar()) as jar:
   names=[n for n in jar.namelist() if n.startswith('src/') and n.endswith('.java')]
   if op=='local_source_read':
    if args['path'] not in names:raise ValueError('Unknown bundled source path')
    lines=jar.read(args['path']).decode('utf-8',errors='replace').splitlines();start=args.get('start',1);count=args.get('count',150);return {'path':args['path'],'total_lines':len(lines),'start':start,'text':'\n'.join(f'{i+1}: {lines[i]}' for i in range(start-1,min(start-1+count,len(lines))))}
   results=[];query=args['query'].lower();part=args.get('path_contains','').lower()
   for name in names:
    if part not in name.lower():continue
    for i,line in enumerate(jar.read(name).decode('utf-8',errors='replace').splitlines(),1):
     if query in line.lower():
      results.append({'path':name,'line':i,'text':line.strip()[:400]})
      if len(results)>=args.get('limit',20):return results
   return results
 if op in ('local_mem_export','local_mem_import'):
  path=Path(args['path']).resolve()
  if not path.is_relative_to(workspace()):raise ValueError('Path outside workspace')
  if op=='local_mem_export':
   if path.exists():raise ValueError('Destination exists')
   data=rpc('memory',project=args['project'],id=args['id'],action='read',start=args.get('start',0),count=args['count'])
   path.write_text('v2.0 raw\n'+'\n'.join(' '.join(f'{x:x}' for x in data['values'][i:i+16]) for i in range(0,len(data['values']),16))+'\n',encoding='ascii');return {'path':str(path),'words':len(data['values'])}
  text=path.read_text(encoding='ascii');lines=[line.split('#',1)[0].strip() for line in text.splitlines()];lines=[x for x in lines if x]
  if not lines or lines[0]!='v2.0 raw':raise ValueError('Expected v2.0 raw header')
  values=[]
  for word in ' '.join(lines[1:]).split():
   count,sep,value=word.partition('*');n=int(count,10) if sep else 1;hexword=value if sep else count
   if n<0 or len(values)+n>65536:raise ValueError('Import exceeds bounded 65536-word call')
   number=int(hexword,16)
   if not 0<=number<=4294967295:raise ValueError('Invalid unsigned word')
   values.extend([number]*n)
  return rpc('memory',project=args['project'],id=args['id'],action='write',start=args.get('start',0),count=min(16,len(values)),values=values)
 if op=='local_classes':
  classes=json.loads((BASE/'class-index.json').read_text());matches=[c for c in classes if args.get('query','').lower() in c.lower()];offset=max(0,args.get('offset',0));limit=max(1,min(1000,args.get('limit',50)));return {'total':len(matches),'classes':matches[offset:offset+limit]}
 if op in ('local_read','local_search'):
  docs=json.loads((BASE/'manual-index.json').read_text(encoding='utf-8'))
  if op=='local_read':
   for doc in docs:
    if doc['path']==args['path']:return doc
   raise ValueError('Unknown manual page')
  words=args['query'].lower().split();matches=[d for d in docs if all(w in d['text'].lower() for w in words)];return [{'path':d['path'],'title':d['title'],'excerpt':d['text'][:600]} for d in matches[:max(1,min(args.get('limit',10),50))]]
 return rpc(op,**args)

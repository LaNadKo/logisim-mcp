"""Logisim MCP stdio server. Python standard library; stdout is JSON-RPC only."""
import json,sys
from pathlib import Path
import workbench
from runtime import VERSION
BASE=Path(__file__).resolve().parent
GUIDANCE_URI='logisim://guidance/agents'
def agent_instructions():return (BASE/'AGENT_GUIDE.md').read_text(encoding='utf-8')
PROTOCOLS=('2025-06-18','2025-03-26','2024-11-05')
TOOLS=list(workbench.TOOLS)
BY_NAME={t['name']:t for t in TOOLS}
class RPCError(Exception):
 def __init__(self,code,message):super().__init__(message);self.code=code
def validate(value,schema,path='arguments'):
 if 'anyOf' in schema:
  for option in schema['anyOf']:
   try:validate(value,option,path);return
   except ValueError:pass
  raise ValueError(path+': no matching type')
 typ=schema.get('type')
 types={'object':lambda v:isinstance(v,dict),'array':lambda v:isinstance(v,list),'string':lambda v:isinstance(v,str),'integer':lambda v:isinstance(v,int) and not isinstance(v,bool),'number':lambda v:isinstance(v,(int,float)) and not isinstance(v,bool),'boolean':lambda v:isinstance(v,bool)}
 if typ and not types[typ](value):raise ValueError(f'{path}: expected {typ}')
 if 'enum' in schema and value not in schema['enum']:raise ValueError(path+': invalid enum value')
 if typ=='object':
  for k in schema.get('required',[]):
   if k not in value:raise ValueError(path+': missing '+k)
  for k,v in value.items():
   if k in schema.get('properties',{}):validate(v,schema['properties'][k],path+'.'+k)
   elif schema.get('additionalProperties') is False:raise ValueError(path+': unknown key '+k)
   elif isinstance(schema.get('additionalProperties'),dict):validate(v,schema['additionalProperties'],path+'.'+k)
 if typ=='array':
  if len(value)<schema.get('minItems',0) or len(value)>schema.get('maxItems',100000):raise ValueError(path+': invalid array length')
  for i,v in enumerate(value):validate(v,schema.get('items',{}),path+f'[{i}]')
 if typ in ('number','integer'):
  if 'minimum' in schema and value<schema['minimum'] or 'maximum' in schema and value>schema['maximum'] or 'exclusiveMinimum' in schema and value<=schema['exclusiveMinimum']:raise ValueError(path+': out of range')
def call(name,args):
 if name not in BY_NAME:raise ValueError('Unknown tool '+name)
 validate(args,BY_NAME[name]['inputSchema'])
 if name in workbench.OPS:return workbench.call(name,args)
 raise ValueError('No implementation for '+name)
def docs():return json.loads((BASE/'manual-index.json').read_text(encoding='utf-8'))
def dispatch(msg):
 method=msg.get('method');params=msg.get('params',{})
 if method=='initialize':
  requested=params.get('protocolVersion');return {'protocolVersion':requested if requested in PROTOCOLS else PROTOCOLS[0],'capabilities':{'tools':{},'resources':{}},'serverInfo':{'name':'logisim-live','version':VERSION},'instructions':agent_instructions()}
 if method=='ping':return {}
 if method=='tools/list':return {'tools':TOOLS}
 if method=='tools/call':
  try:
   result=call(params['name'],params.get('arguments',{}))
   return {'content':[{'type':'text','text':result if isinstance(result,str) else json.dumps(result,ensure_ascii=False)}]}
  except Exception as e:return {'isError':True,'content':[{'type':'text','text':str(e)}]}
 if method=='resources/list':return {'resources':[{'uri':GUIDANCE_URI,'name':'Agent workflow: full implementation, no unrequested simplification','mimeType':'text/markdown'}]+[{'uri':'logisim://manual/'+d['path'],'name':d['title'],'mimeType':'text/plain'} for d in docs()]+[{'uri':'logisim://api/classes','name':'Native class index','mimeType':'application/json'}]}
 if method=='resources/read':
  uri=params.get('uri','')
  if uri==GUIDANCE_URI:return {'contents':[{'uri':uri,'mimeType':'text/markdown','text':agent_instructions()}]}
  if uri=='logisim://api/classes':text=(BASE/'class-index.json').read_text()
  else:
   match=[d for d in docs() if uri=='logisim://manual/'+d['path']]
   if not match:raise RPCError(-32002,'Unknown resource')
   text=match[0]['text']
  return {'contents':[{'uri':uri,'mimeType':'text/plain','text':text}]}
 raise RPCError(-32601,'Unknown method')
def serve():
 sys.stdin.reconfigure(encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8')
 from connect import connect
 try:connect()
 except Exception as e:print('Live connection unavailable: '+str(e),file=sys.stderr)
 initialized=False;ready=False
 for line in sys.stdin:
  msg=None
  try:
   if len(line)>1048576:raise RPCError(-32600,'Request too large')
   try:msg=json.loads(line)
   except ValueError:raise RPCError(-32700,'Parse error')
   if not isinstance(msg,dict) or msg.get('jsonrpc')!='2.0' or not isinstance(msg.get('method'),str):raise RPCError(-32600,'Invalid request')
   if 'id' not in msg:
    if msg['method']=='notifications/initialized':ready=initialized
    continue
   if msg['method']=='initialize':
    if initialized:raise RPCError(-32600,'Already initialized')
    result=dispatch(msg);initialized=True
   else:
    if msg['method']!='ping' and not ready:raise RPCError(-32002,'Initialize first')
    result=dispatch(msg)
   response={'jsonrpc':'2.0','id':msg['id'],'result':result}
  except RPCError as e:response={'jsonrpc':'2.0','id':msg.get('id') if isinstance(msg,dict) else None,'error':{'code':e.code,'message':str(e)}}
  except Exception as e:response={'jsonrpc':'2.0','id':msg.get('id') if isinstance(msg,dict) else None,'error':{'code':-32603,'message':str(e)}}
  print(json.dumps(response,ensure_ascii=False),flush=True)
if __name__=='__main__':serve()

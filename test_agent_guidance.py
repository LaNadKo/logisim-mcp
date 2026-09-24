"""Read-only MCP contract checks: no edits, test circuits or simulation changes."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

BASE=Path(__file__).resolve().parent

class AgentGuidanceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  requests=[
   {'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'guidance-check','version':'1'}}},
   {'jsonrpc':'2.0','method':'notifications/initialized'},
   {'jsonrpc':'2.0','id':2,'method':'resources/list'},
   {'jsonrpc':'2.0','id':3,'method':'resources/read','params':{'uri':'logisim://guidance/agents'}},
   {'jsonrpc':'2.0','id':4,'method':'tools/list'},
   {'jsonrpc':'2.0','id':5,'method':'resources/read','params':{'uri':'logisim://missing'}},
  ]
  process=subprocess.run([sys.executable,str(BASE/'mcp_server.py')],input='\n'.join(json.dumps(r) for r in requests)+'\n',text=True,encoding='utf-8',capture_output=True,timeout=30)
  if process.returncode:raise RuntimeError(process.stderr)
  cls.responses={r['id']:r for r in map(json.loads,process.stdout.splitlines())}
  cls.guide=(BASE/'AGENT_GUIDE.md').read_text(encoding='utf-8')

 def test_full_instructions_delivered_at_initialize(self):
  self.assertEqual(set(self.responses),{1,2,3,4,5})
  result=self.responses[1]['result']
  self.assertEqual(result['instructions'],self.guide)
  self.assertEqual(result['serverInfo']['version'],'1.0.0')
  self.assertEqual(result['protocolVersion'],'2025-06-18')

 def test_resource_discoverable_and_readable(self):
  resources=self.responses[2]['result']['resources']
  self.assertEqual(len(resources),131)
  entry=next(r for r in resources if r['uri']=='logisim://guidance/agents')
  self.assertEqual(entry['mimeType'],'text/markdown')
  self.assertEqual(self.responses[3]['result']['contents'],[{'uri':entry['uri'],'mimeType':'text/markdown','text':self.guide}])
  self.assertEqual(self.responses[5]['error']['code'],-32002)

 def test_tools_preserved_and_synthesis_points_to_guidance(self):
  tools=self.responses[4]['result']['tools']
  self.assertEqual(len(tools),54)
  self.assertEqual(tools,json.loads((BASE/'tools.json').read_text(encoding='utf-8')))
  for name in ['analyzer_minimize','analyzer_build']:
   self.assertIn('logisim://guidance/agents',next(t['description'] for t in tools if t['name']==name))

if __name__=='__main__':unittest.main()

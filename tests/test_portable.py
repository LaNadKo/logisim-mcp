import contextlib,hashlib,io,json,os,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
import runtime
from mcp_server import dispatch,call

class PortableTests(unittest.TestCase):
 def test_runtime_platforms(self):
  for system,machine,key in [('Windows','AMD64','windows-x64'),('Linux','x86_64','linux-x64'),('Linux','aarch64','linux-arm64'),('Darwin','x86_64','macos-x64'),('Darwin','arm64','macos-arm64')]:
   with patch('platform.system',return_value=system),patch('platform.machine',return_value=machine):self.assertEqual(runtime.platform_key(),key)
 def test_unsupported_platform(self):
  with patch('platform.system',return_value='FreeBSD'),self.assertRaises(RuntimeError):runtime.platform_key()
 def test_relative_paths_survive_move(self):
  with tempfile.TemporaryDirectory(prefix='portable path ') as d,patch.object(runtime,'BASE',Path(d)),patch.dict(os.environ,{},clear=True):
   self.assertEqual(runtime.workspace(),Path(d).resolve()/'workspace')
   self.assertEqual(runtime.connection_file(),Path(d).resolve()/'.state/connection.json')
 def test_environment_override(self):
  with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'LOGISIM_MCP_WORKSPACE':d}):self.assertEqual(runtime.workspace(),Path(d).resolve())
 def test_build_info_is_relative_and_exists(self):
  data=json.loads((BASE/'build-info.json').read_text());self.assertFalse(Path(data['jar']).is_absolute())
  with zipfile.ZipFile(BASE/data['jar']) as z:
   manifest=z.read('META-INF/MANIFEST.MF').decode();self.assertIn('Premain-Class: '+data['class'],manifest)
   self.assertIn('Agent-Class: '+data['class'],manifest)
   self.assertIn(data['class']+'.class',z.namelist())
 def test_logisim_source_and_provenance(self):
  with zipfile.ZipFile(runtime.logisim_jar()) as z:
   self.assertIsNone(z.testzip());self.assertIn('COPYING.TXT',z.namelist());self.assertIn('src/com/cburch/logisim/Main.java',z.namelist())
  meta=json.loads((BASE/'vendor/logisim-provenance.json').read_text())
  self.assertEqual(hashlib.sha256(runtime.logisim_jar().read_bytes()).hexdigest(),meta['jar_sha256'])
 def test_guidance_in_protocol(self):
  result=dispatch({'method':'initialize','params':{'protocolVersion':'2025-06-18'}})
  self.assertEqual(result['instructions'],(BASE/'AGENT_GUIDE.md').read_text(encoding='utf-8'))
  self.assertEqual(result['serverInfo']['version'],runtime.VERSION)
  resources=dispatch({'method':'resources/list'})['resources'];self.assertEqual(len(resources),131)
  guide=dispatch({'method':'resources/read','params':{'uri':'logisim://guidance/agents'}})
  self.assertEqual(guide['contents'][0]['text'],result['instructions'])
 def test_tool_catalog_matches(self):self.assertEqual(dispatch({'method':'tools/list'})['tools'],json.loads((BASE/'tools.json').read_text()))
 def test_bad_schema_rejected_before_connection(self):
  with self.assertRaises(ValueError):call('circuit_edit',{'project':'unused','actions':'invalid'})
 def test_mixed_attribute_batch_rejected_before_connection(self):
  with self.assertRaisesRegex(ValueError,'cannot safely mix'):
   call('circuit_edit',{'project':'unused','actions':[{'kind':'attribute','id':'x','key':'label','value':'test'},{'kind':'move','id':'x','x':100,'y':100}]})
 def test_lock_has_five_platforms_and_pinned_hashes(self):
  lock=json.loads((BASE/'dependencies.lock.json').read_text());self.assertEqual(len(lock['platforms']),5)
  for parts in lock['platforms'].values():
   for entry in parts.values():
    self.assertRegex(entry['sha256'],r'^[0-9a-f]{64}$');self.assertTrue(entry['url'].startswith('https://github.com/'));self.assertNotIn('/latest/',entry['url'])
  expected=''.join(e['sha256']+' '+e['path']+'\n' for p in lock['platforms'].values() for e in p.values())
  self.assertEqual((BASE/'runtime-archives/SHA256SUMS').read_text(),expected)
 def test_shell_launcher_has_lf(self):
  for name in ['launch.sh','runtime-archives/SHA256SUMS']:self.assertNotIn(b'\r',(BASE/name).read_bytes())

if __name__=='__main__':unittest.main()

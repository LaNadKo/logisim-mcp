from html.parser import HTMLParser
from zipfile import ZipFile
from pathlib import Path
import json,re,hashlib
from runtime import logisim_jar
class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[]
 def handle_data(self,data):self.parts.append(data)
base=Path(__file__).resolve().parent
jar=logisim_jar()
with ZipFile(jar) as z:
 docs=[]
 for name in z.namelist():
  if name.startswith('doc/en/html/') and name.endswith('.html'):
   raw=z.read(name).decode('utf-8',errors='replace');p=Text();p.feed(raw)
   title=re.search(r'<title>(.*?)</title>',raw,re.S|re.I)
   docs.append({'path':name,'title':re.sub(r'\s+',' ',title.group(1)).strip() if title else name,'text':re.sub(r'\s+',' ',' '.join(p.parts)).strip()})
 classes=sorted(n[:-6].replace('/','.') for n in z.namelist() if n.startswith('com/cburch/') and n.endswith('.class') and '$' not in n)
(base/'manual-index.json').write_text(json.dumps(docs,ensure_ascii=False,indent=2),encoding='utf-8')
(base/'class-index.json').write_text(json.dumps(classes,indent=2),encoding='utf-8')
print(json.dumps({'manual_pages':len(docs),'top_level_classes':len(classes),'logisim_sha256':hashlib.sha256(jar.read_bytes()).hexdigest()}))

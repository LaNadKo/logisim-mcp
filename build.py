"""Rebuild portable Java artifacts with a JDK, without attaching to any JVM."""
import hashlib,json,subprocess,zipfile
from runtime import BASE,java_executable,logisim_jar,process_options
def build():
    names=['Workbench.java','LiveBridge.java','LogisimBridge.java','Attach.java']
    digest=hashlib.sha256(b''.join((BASE/n).read_text(encoding='utf-8-sig').encode('utf-8') for n in names)).hexdigest()[:12];name='Workbench_'+digest
    root=BASE/'build'/digest;root.mkdir(parents=True,exist_ok=True);classes=root/'classes';classes.mkdir(exist_ok=True)
    source=(BASE/'Workbench.java').read_text(encoding='utf-8-sig')
    versioned=root/(name+'.java');versioned.write_text(source.replace('Workbench',name).replace('BUILD_ID',digest),encoding='utf-8')
    subprocess.run([java_executable('javac'),'--release','8','-encoding','UTF-8','-cp',str(logisim_jar()),'-d',str(classes),str(BASE/'LogisimBridge.java'),str(BASE/'LiveBridge.java'),str(versioned)],check=True,**process_options())
    helper=root/'helper';helper.mkdir(exist_ok=True)
    subprocess.run([java_executable('javac'),'--release','11','-encoding','UTF-8','-d',str(helper),str(BASE/'Attach.java')],check=True,**process_options())
    lib=BASE/'lib';lib.mkdir(exist_ok=True)
    def archive(path,files,manifest):
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as jar:
            jar.writestr('META-INF/MANIFEST.MF',manifest)
            for file in sorted(files.rglob('*.class')):jar.write(file,file.relative_to(files).as_posix())
    agent=lib/f'agent-{digest}.jar'
    archive(agent,classes,f'Manifest-Version: 1.0\nAgent-Class: {name}\nPremain-Class: {name}\n\n')
    archive(lib/'attach.jar',helper,'Manifest-Version: 1.0\nMain-Class: Attach\n\n')
    (BASE/'build-info.json').write_text(json.dumps({'build':digest,'jar':agent.relative_to(BASE).as_posix(),'class':name},indent=2)+'\n',encoding='utf-8');print('Built '+agent.name)
if __name__=='__main__':build()

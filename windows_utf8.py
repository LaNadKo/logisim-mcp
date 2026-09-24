"""Give a private copy of a bundled JDK launcher a UTF-8 process manifest.

JDK 17 uses ANSI Windows APIs to locate native DLLs. UTF-8 is enabled for
this executable only; the original vendor executable and OS locale stay intact.
Requires Windows 10 1903 or later. No compiler or administrator rights needed.
"""
from pathlib import Path
import ctypes, hashlib, json, os, shutil, uuid
from ctypes import wintypes as w
from xml.etree import ElementTree as ET


def prepare(executable):
    source=Path(executable)
    target=source.with_name(source.stem+'-logisim-utf8.exe')
    marker=target.with_suffix('.json')
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    try:
        cached=json.loads(marker.read_text(encoding='utf-8'))
        if cached['source']==digest and cached['format']==1 and cached['output']==hashlib.sha256(target.read_bytes()).hexdigest():
            return str(target)
    except (OSError,ValueError,KeyError):pass
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    signatures={
        'LoadLibraryExW':([w.LPCWSTR,w.HANDLE,w.DWORD],w.HMODULE),
        'FindResourceExW':([w.HMODULE,w.LPCVOID,w.LPCVOID,w.WORD],w.HRSRC),
        'SizeofResource':([w.HMODULE,w.HRSRC],w.DWORD),
        'LoadResource':([w.HMODULE,w.HRSRC],w.HGLOBAL),
        'LockResource':([w.HGLOBAL],w.LPVOID),
        'FreeLibrary':([w.HMODULE],w.BOOL),
        'BeginUpdateResourceW':([w.LPCWSTR,w.BOOL],w.HANDLE),
        'UpdateResourceW':([w.HANDLE,w.LPCVOID,w.LPCVOID,w.WORD,w.LPVOID,w.DWORD],w.BOOL),
        'EndUpdateResourceW':([w.HANDLE,w.BOOL],w.BOOL),
    }
    for name,(args,result) in signatures.items():
        fn=getattr(kernel,name);fn.argtypes=args;fn.restype=result
    def checked(value):
        if not value:raise ctypes.WinError(ctypes.get_last_error())
        return value
    handle=checked(kernel.LoadLibraryExW(str(source),None,2))
    try:
        # Pinned Temurin Windows launchers use manifest ID 1, English (US).
        resource=checked(kernel.FindResourceExW(handle,24,1,1033))
        size=checked(kernel.SizeofResource(handle,resource))
        address=checked(kernel.LockResource(checked(kernel.LoadResource(handle,resource))))
        root=ET.fromstring(ctypes.string_at(address,size))
    finally:kernel.FreeLibrary(handle)
    asm='urn:schemas-microsoft-com:asm.v3'
    application=root.find('{'+asm+'}application')
    if application is None:application=ET.SubElement(root,'{'+asm+'}application')
    settings=application.find('{'+asm+'}windowsSettings')
    if settings is None:settings=ET.SubElement(application,'{'+asm+'}windowsSettings')
    ET.SubElement(settings,'{http://schemas.microsoft.com/SMI/2019/WindowsSettings}activeCodePage').text='UTF-8'
    manifest=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    temporary=target.with_name(target.stem+'-'+uuid.uuid4().hex+'.exe')
    try:
        shutil.copy2(source,temporary)
        update=checked(kernel.BeginUpdateResourceW(str(temporary),False))
        try:
            checked(kernel.UpdateResourceW(update,24,1,1033,ctypes.create_string_buffer(manifest),len(manifest)))
        except BaseException:
            kernel.EndUpdateResourceW(update,True);raise
        checked(kernel.EndUpdateResourceW(update,False))
        output=hashlib.sha256(temporary.read_bytes()).hexdigest()
        # Concurrent clients may have already published the same derived launcher.
        if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest()!=output:
            os.replace(temporary,target)
        marker.write_text(json.dumps({'format':1,'source':digest,'output':output}),encoding='utf-8')
        return str(target)
    finally:temporary.unlink(missing_ok=True)

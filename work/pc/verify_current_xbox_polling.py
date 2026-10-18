from pathlib import Path
import ctypes as C,hashlib,json,os,subprocess
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');base=Path(r'C:\NFSUG-Workspace\NFSUG-Xbox-Polling-20261017');base.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
host=root/'work/pc/live_host.c';header=root/'outputs/nfsug-research/controller.h';text=host.read_text(encoding='utf8')
def function(signature):
 start=text.index(signature);brace=text.index('{',start);depth=1;end=brace+1
 while depth:
  depth+=(text[end]=='{')-(text[end]=='}');end+=1
 return text[start:end]
functions='\n'.join(function(s) for s in ['static int controller_check(void)','static unsigned input(int*connected)'])
cases=Path(__file__).with_name('xbox_poll_cases.c').read_text(encoding='utf8')
source='#define WIN32_LEAN_AND_MEAN\n#include <windows.h>\n#include <xinput.h>\n#include <stdint.h>\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n'+header.read_text(encoding='utf8')+'\n'+cases.replace('/* HOST_FUNCTIONS */',functions)
(base/'current-host-input-test.c').write_text(source,encoding='utf8')
command=['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-O2','-Wall','-Wextra','-Werror',str(base/'current-host-input-test.c'),'-o',str(base/'current-host-input-test.exe')]
env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;'+env['PATH']
compiled=subprocess.run(command,capture_output=True,env=env);(base/'compile.log').write_bytes(compiled.stdout+compiled.stderr);assert compiled.returncode==0,(base/'compile.log').read_text()
test=subprocess.run([str(base/'current-host-input-test.exe')],capture_output=True,env=env);(base/'run.log').write_bytes(test.stdout+test.stderr);assert test.returncode==0,test.stderr.decode()
report=json.loads(test.stdout);assert report['checks']>=40
class Pad(C.Structure):_fields_=[('buttons',C.c_uint16),('lt',C.c_uint8),('rt',C.c_uint8),('lx',C.c_int16),('ly',C.c_int16),('rx',C.c_int16),('ry',C.c_int16)]
class State(C.Structure):_fields_=[('packet',C.c_uint32),('pad',Pad)]
assert C.sizeof(State)==16
library=None
for name in ['xinput1_4.dll','xinput9_1_0.dll']:
 try:library=C.WinDLL(name);loaded=name;break
 except OSError:pass
devices=[]
if library:
 get=library.XInputGetState;get.argtypes=[C.c_uint32,C.POINTER(State)];get.restype=C.c_uint32
 for slot in range(4):
  state=State();status=int(get(slot,C.byref(state)));devices.append(dict(slot=slot,result=status,connected=status==0))
report.update(host_source_sha256=sha(host),controller_header_sha256=sha(header),exact_host_functions_sha256=hashlib.sha256(functions.encode()).hexdigest(),compiled_source_sha256=sha(base/'current-host-input-test.c'),test_exe_sha256=sha(base/'current-host-input-test.exe'),compile_command=command,read_only_xinput_detection=dict(library=loaded if library else None,slots=devices),scope='Exact current PC host input() and startup mapping check compiled with controlled Windows polling callbacks. No physical button presses, foreground Windows event delivery, game-response integration, audio, rendering or FPS proof.')
(base/'controller-polling-report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))

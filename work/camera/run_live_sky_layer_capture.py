"""Bounded live queued draw readbacks; deliberately unsuitable for cadence claims."""
import ctypes as C, hashlib, json, math, runpy, struct, time
from pathlib import Path
import live_native_batch_candidate as batch
saved_address=batch.callback_address
owners=[];captures=[];calls=0;errors=[]
gl=C.WinDLL('opengl32')
gl.glReadPixels.argtypes=[C.c_int,C.c_int,C.c_int,C.c_int,C.c_uint,C.c_uint,C.c_void_p]
gl.glPixelStorei.argtypes=[C.c_uint,C.c_int]
strip=C.create_string_buffer(3240*3)
prestrip=C.create_string_buffer(3240*3)
gpu=C.CDLL(str(Path('work/camera/owned-sky-row-diagnostic.dll').resolve()))
gpu.nf_owned_gpu_sky_row_read.argtypes=[C.c_void_p,C.c_size_t]
def address(function):
 if getattr(function,'__name__','')!='nf_owned_gpu_draw_context_callback':return saved_address(function)
 function.argtypes=[C.c_void_p]
 def draw(ptr):
  global calls
  calls+=1;assert gpu.nf_owned_gpu_sky_row_mode(int(40<=calls<340))==0
  result=function(ptr)
  if result or not 40<=calls<340:return result
  try:
   ctx=C.cast(ptr,C.POINTER(batch.DrawContext)).contents
   if not ctx.skycount:return result
   gl.glPixelStorei(0x0D05,1);gl.glReadPixels(300,2160-1-int(44.5*13.5),3240,1,0x1907,0x1401,strip)
   assert gl.glGetError()==0
   frame=C.string_at(ctx.frame,40);gn=struct.unpack_from('<I',frame,8)[0]
   palette=struct.unpack('<256H',C.string_at(ctx.frame+40+gn+44*34944+128+32768,512))
   lower=C.string_at(ctx.lower,240);upper=C.string_at(ctx.upper,240)
   assert gpu.nf_owned_gpu_sky_row_read(prestrip,len(prestrip))==0
   expected=bytearray();actual=bytearray();background=bytearray()
   for x in range(240):
    ca=palette[lower[x]];cb=palette[upper[x]]
    for shift in (0,5,10):
     a=(ca>>shift)&31;b=(cb>>shift)&31;a=(a<<3)|(a>>2);b=(b<<3)|(b>>2)
     expected.append(math.floor(a+(b-a)*ctx.weight+.5))
    at=int((x+.5)*13.5)*3;actual.extend(strip.raw[at:at+3]);background.extend(prestrip.raw[at:at+3])
   captures.append(dict(draw_started_ns=ctx.started_ns,weight=ctx.weight,actual=actual.hex(),expected=expected.hex(),background=background.hex(),source_lower_sha256=hashlib.sha256(lower).hexdigest(),source_upper_sha256=hashlib.sha256(upper).hexdigest()))
  except Exception as e:errors.append(repr(e));return 39
  return result
 callback=batch.Callback(draw);owners.append(callback);return saved_address(callback)
batch.callback_address=address
try:runpy.run_path('work/camera/run_sky_row_renderer_diagnostic.py',run_name='__main__')
finally:
 out=Path('work/camera/prototype-runs')/('live-sky-pixels-'+str(time.time_ns())+'.json')
 out.write_text(json.dumps(dict(captures=captures,errors=errors,draw_calls=calls,scope='Live queued fullscene selected draw target, 240 native pixel centers in original sky row44. May include foreground/HUD occlusion. Draw timestamp must join committed sample before interpretation. Readback and Python callback overhead invalidate cadence comparison.'),indent=2));print(out)

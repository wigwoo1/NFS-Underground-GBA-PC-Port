from pathlib import Path
import struct,subprocess,os,json,hashlib
p=Path('work/camera');a=p/'motion-actual-scanline-assets';exe=str((p/'owned-wall-gpu-preview.exe').resolve());checks=[]
for r in (8758,8762,8766,8769,8773,8776,8780):
 packet=a/f'{r}-native-complete-frame.bin';raw=packet.read_bytes();assert raw==(a/f'{r}-owned-timed-frame.bin').read_bytes();magic,refresh,gn,hn,bn,tn,epoch,ticks=struct.unpack_from('<6I2Q',raw);assert magic==0x3346474e and refresh==r and epoch and ticks==r*280896
 out=p/f'owned-timed-{r}.ppm';ref=p/f'owned-reference-{r}.ppm'
 env={**os.environ,'NF_GPU_EXPECT_EPOCH':str(epoch)}
 run=subprocess.run([exe,str(packet),str(out)],env=env,capture_output=True,text=True);assert run.returncode==0,(r,run.stderr)
 run=subprocess.run([exe,str(a/f'{r}-owned-background-frame.bin'),str(ref)],capture_output=True,text=True);assert run.returncode==0
 assert out.read_bytes()==ref.read_bytes(),r
 checks.append(dict(refresh=r,epoch=epoch,simulation_cycles=ticks,identical_rgb=True))
base=bytearray((a/'8758-owned-timed-frame.bin').read_bytes());epoch=struct.unpack_from('<Q',base,24)[0];bad=p/'owned-timed-invalid.bin';out=p/'owned-timed-rejected.ppm'
assert not out.exists()
for name,raw,expected,env in [('stale_epoch',base,29,{**os.environ,'NF_GPU_EXPECT_EPOCH':str(epoch+1)}),('wrong_cycles',bytearray(base),28,os.environ),('bad_coverage',bytearray(base),25,os.environ)]:
 if name=='wrong_cycles':struct.pack_into('<Q',raw,32,0)
 if name=='bad_coverage':raw[-1]=2
 bad.write_bytes(raw);run=subprocess.run([exe,str(bad),str(out)],env=env,capture_output=True,text=True);assert run.returncode==expected and not out.exists() and 'native_gl' not in run.stderr,(name,run.returncode)
report=dict(result='PASS_OWNED_TIMED_FRAME_GPU',checks=checks,rejections=['stale_epoch','wrong_cycles','bad_coverage'],clock_hz=16777216,cycles_per_refresh=280896,scope='Diagnostic complete-frame handoff identity and original-cycle metadata; no live scheduling/interpolation or60fps gameplay proof.')
(p/'owned-timed-frame-tests.json').write_text(json.dumps(report,indent=2));print(report)

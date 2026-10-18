from pathlib import Path
import struct,subprocess,json,sys
sys.path.insert(0,'work/pydeps')
import numpy as np
p=Path('work/camera').resolve();fixture=next((p/'packet-sequence').glob('scene-*.packet')).read_bytes()
def section(i):
 off,size=struct.unpack_from('<2I',fixture,36+i*12);return fixture[off:off+size]
model=bytearray(section(0));w,h=struct.unpack_from('<2I',model,16);pixels=w*h;start=len(model)-pixels*4
red=bytes((255,0,0,255));blue=bytes((0,0,255,255));indices=bytes((i+i//w)%2 for i in range(pixels))
for i,index in enumerate(indices):model[start+i*4:start+i*4+4]=blue if index else red
colors=[((y*3)%32)|(((y*7)%32)<<5)|(((y*11)%32)<<10) for y in range(160)]
colorfile=p/'zero-gpu-rows.bin';colorfile.write_bytes(struct.pack('<160H',*colors))
def packet(asset):
 sections=[asset,struct.pack('<2I',0x31444652,0),struct.pack('<3I',0x314f464e,1,0xffffffff),struct.pack('<2I',0x314c464e,0)+section(3)[-131072:],struct.pack('<2I',0x3149464e,1)+section(4)[-20:]]
 raw=bytearray(96);struct.pack_into('<8I',raw,0,0x3150534e,1,0,5,100,99,100,0)
 for i,s in enumerate(sections):
  raw.extend(bytes((-len(raw))%8));struct.pack_into('<3I',raw,32+i*12,i+1,len(raw),len(s));raw.extend(s)
 struct.pack_into('<I',raw,8,len(raw));return raw
def render(name,asset):
 path=p/f'zero-gpu-{name}.packet';prefix=p/f'zero-gpu-{name}';path.write_bytes(packet(asset))
 result=subprocess.run([str(p/'zero-snapshot-preview.exe'),str(path),str(prefix),str(colorfile)],capture_output=True,text=True)
 assert result.returncode==0,(name,result.returncode,result.stdout,result.stderr)
 data=Path(str(prefix)+'-0.ppm').read_bytes();return np.frombuffer(data.split(b'\n',3)[3],dtype=np.uint8).reshape(2160,3840,3)
baseline=render('baseline',model)
background_rgba=np.frombuffer((p/'zero-gpu-baseline.rgba').read_bytes(),dtype=np.uint8).reshape(2160,3840,4)[::-1]
for y in range(2160):
 row=int((y+0.5)/13.5);c=colors[row];rgb=[(((c>>(k*5))&31)<<3)|(((c>>(k*5))&31)>>2) for k in range(3)]
 assert list(background_rgba[y,310])==rgb+[0],('sky row',y,list(background_rgba[y,310]),rgb)
assert np.all(background_rgba[:,0,3]==255),'sidebar state changed'
tag=lambda data:bytes(model)+struct.pack('<4I',0x31495a4e,w,h,0)+data
tagged=render('mixed',tag(indices));mask=np.all(baseline==[255,0,0],axis=2);assert mask.sum()>100
expected=baseline.copy()
for y in range(2160):
 row=int((y+0.5)/13.5);c=colors[row];rgb=[(((c>>(k*5))&31)<<3)|(((c>>(k*5))&31)>>2) for k in range(3)]
 expected[y,mask[y]]=rgb
assert np.array_equal(tagged,expected),('mixed pixel mismatch',int(np.any(tagged!=expected,axis=2).sum()))
coverage=np.frombuffer((p/'zero-gpu-mixed.rgba').read_bytes(),dtype=np.uint8).reshape(2160,3840,4)[::-1,:,3]
assert np.all(coverage[mask]==0),'index0 must clear BG2 coverage instead of discarding'
nonzero_mask=np.all(baseline==[0,0,255],axis=2)
assert np.all(coverage[nonzero_mask]==255),'nonzero BG2 coverage must remain opaque'
nonzero=render('nonzero',tag(bytes([1])*pixels));assert np.array_equal(nonzero,baseline)
report=dict(result='PASS',exact_4k_pixels=2*3840*2160,zero_pixels_recolored=int(mask.sum()),nonzero_unchanged=True,exact_backdrop_rows=2160,backdrop_bg2_coverage=False,zero_bg2_coverage_cleared=int(mask.sum()),nonzero_bg2_coverage_preserved=int(nonzero_mask.sum()),scope='Offscreen model shader with synthetic owned index metadata and160row colors; perspective texture sampling, framebuffer-zero overwrite with transparent BG2 display coverage andnonzero preservation. Synthetic scanline backdrop verified; live full-scene fidelity andtiming remain unverified.')
(p/'model-zero-gpu-tests.json').write_text(json.dumps(report,indent=2));print(report)

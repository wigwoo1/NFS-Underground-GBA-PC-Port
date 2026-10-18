"""Read actual GPU texel coordinates at the previously isolated boundary sample."""
import hashlib,json,os,subprocess,struct,sys
from pathlib import Path
from PIL import Image
p=Path(__file__).resolve().parent; report_path=Path(sys.argv[1]); report=json.loads(report_path.read_text())
samples=[(c,d) for c in report['checks'] for d in c['differences'] if 'uv' in d]; assert len(samples)==1
c,d=samples[0]; packet=p/'visibility-original-859.packet'; data=packet.read_bytes(); assert hashlib.sha256(data).hexdigest()==c['packet_sha256']
env={k:v for k,v in os.environ.items() if not k.startswith('NF_')};env.update(NF_ENDPOINT_COMMANDS=str(c['command']),NF_CONTINUOUS_ROAD_UV='1',NF_ROAD_RECIPROCAL=str(p/'road-correction-reciprocal.bin'))
target=p/'prototype-runs/sign-boundary-texel.ppm'; exe=p/'endpoint-sign-texel-preview.exe'
subprocess.run([str(exe),str(packet),str(target)],env=env,check=True,capture_output=True)
pixel=list(Image.open(str(target)+'-0.ppm').getpixel(tuple(d['physical_pixel']))); assert pixel[2]==255
sections={t:data[o:o+n] for t,o,n in (struct.unpack_from('<3I',data,32+i*12) for i in range(5))};world=sections[2];at=8
for i in range(c['command']+1):
 n,w,h=struct.unpack_from('<3I',world,at)
 if i==c['command']:texture=world[at+12+n*40:at+12+n*40+w*h*4]
 at+=12+n*40+w*h*4
tx,ty=pixel[:2]; color=list(texture[(ty*w+tx)*4:(ty*w+tx)*4+3]); assert color==d['actual']
assert [tx,ty]==[21,36] and d['texel']==[21,37]
out=report_path.with_name(report_path.stem+'-boundary.json')
out.write_text(json.dumps(dict(result='PASS',input_report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),diagnostic_renderer_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),packet_sha256=c['packet_sha256'],physical_pixel=d['physical_pixel'],cpu_texel=d['texel'],gpu_texel=[tx,ty],actual_color=color,vertical_distance_to_boundary_texels=(d['uv'][1]*64-37),scope='Compile-time diagnostic shader exposes actual interpolated nearest texel for one opaque GPU sample. Confirms adjacent vertical row selection; does not prove a particular floating-point precision cause or whole-scene fidelity.'),indent=2));print(out.read_text())

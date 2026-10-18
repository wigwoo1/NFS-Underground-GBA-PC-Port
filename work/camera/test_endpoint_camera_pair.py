"""Validate diagnostic camera input rejection and unchanged default image."""
import hashlib,json,os,struct,subprocess
from pathlib import Path
p=Path(__file__).resolve().parent;exe=p/'endpoint-scene-road-order-preview.exe';packet=p/'visibility-original-859.packet';env={k:v for k,v in os.environ.items() if not k.startswith('NF_')};env.update(NF_ENDPOINT_COMMANDS='25',NF_CONTINUOUS_ROAD_UV='1',NF_ROAD_RECIPROCAL=str(p/'road-correction-reciprocal.bin'))
target=p/'prototype-runs/endpoint-camera-default-check.ppm';subprocess.run([str(exe),str(packet),str(target)],env=env,check=True,capture_output=True)
actual=Path(str(target)+'-0.ppm').read_bytes();expected=(p/'prototype-runs/sign-gpu-12350.ppm-0.ppm').read_bytes();assert actual==expected
valid=struct.pack('<14d',0,0,0,0,0,0,1,0,0,0,0,0,0,1);bad_nan=bytearray(valid);struct.pack_into('<d',bad_nan,0,float('nan'));bad_q=bytearray(valid);struct.pack_into('<d',bad_q,48,0)
cases=[]
for name,data in [('short',valid[:-1]),('long',valid+b'X'),('nonfinite',bad_nan),('zero_quaternion',bad_q)]:
 path=p/'prototype-runs'/('endpoint-camera-invalid-'+name+'.bin');path.write_bytes(data);result=subprocess.run([str(exe),str(packet),str(target)],env=dict(env,NF_ENDPOINT_CAMERA_PAIR=str(path)),capture_output=True);assert result.returncode==35;cases.append(dict(case=name,exit_code=result.returncode))
out=p/'prototype-runs/endpoint-camera-pair-tests.json';out.write_text(json.dumps(dict(result='PASS',renderer_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),default_image_sha256=hashlib.sha256(actual).hexdigest(),negative_cases=cases,scope='Diagnostic sidecar validation plus full native RGB default-path regression. Valid camera rendering exercised separately by repeated portal audit.'),indent=2));print(out.read_text())

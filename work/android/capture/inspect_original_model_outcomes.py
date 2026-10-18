from pathlib import Path
import struct,json
p=Path(r'C:\NFSUG-Workspace\NFSUG-android-arm-object-trace-local');rows=list(struct.iter_unpack('<20I',(p/'original-object-path.bin').read_bytes()));calls=[]
for i,row in enumerate(rows):
 if row[2]!=0x03002628:continue
 after=next((r for r in rows[i+1:] if r[2]==0x0300262c),None);assert after is not None;calls.append(dict(frame=row[1],source=row[11],context=row[4],return_frame=after[1],return_r0=after[4]))
report=dict(result='ORIGINAL_MODEL_CALL_RETURN_REGISTERS',calls=calls);(p/'model-call-outcome-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

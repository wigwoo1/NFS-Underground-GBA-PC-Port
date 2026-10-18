from pathlib import Path
import struct,json,sys,collections
sys.path.insert(0,r'C:\NFSUG-Workspace\android-tools\analysis-python');from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_MODE_LITTLE_ENDIAN
folder=Path(r'C:\NFSUG-Workspace\NFSUG-android-object-trace-local');raw=(folder/'original-object-path.bin').read_bytes();assert len(raw)%80==0;rows=list(struct.iter_unpack('<20I',raw));decoder=Cs(CS_ARCH_ARM,CS_MODE_THUMB|CS_MODE_LITTLE_ENDIAN);target=33572092;selected=[];counts=collections.Counter()
for index,row in enumerate(rows):
 serial,frame,pc,op=row[:4];regs=row[4:];assert serial==7
 matching=[i for i,v in enumerate(regs[:13]) if v==target]
 if not matching:continue
 counts.update(matching);instruction=next(decoder.disasm(struct.pack('<H',op&65535),pc),None);selected.append(dict(row=index,frame=frame,pc=hex(pc),op=hex(op&65535),instruction='' if instruction is None else instruction.mnemonic+' '+instruction.op_str,target_registers=matching,registers=list(regs[:13])))
report=dict(result='ORIGINAL_OBJECT_PATH_CAPTURED',records=len(rows),target_register_counts=dict(counts),target_path=selected);(folder/'original-object-path-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(records=len(rows),target_records=len(selected),target_register_counts=dict(counts))));print(json.dumps([{k:r[k] for k in ('row','frame','pc','instruction','target_registers')} for r in selected[-25:]],indent=2))

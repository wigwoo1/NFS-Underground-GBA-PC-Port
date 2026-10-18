"""Check every owned live command portal against its regenerated source command."""
import hashlib,json,struct,sys
from pathlib import Path
trace_path=Path(sys.argv[1]);trace=json.loads(trace_path.read_text());rows=[]
for sample in trace['samples']:
 path=Path(sample['query_fixture'].replace('-query-fixture.bin','-native-scene.bin'));data=path.read_bytes();assert hashlib.sha256(data).hexdigest()==sample['packet_sha256']
 sections={t:data[o:o+n] for t,o,n in (struct.unpack_from('<3I',data,32+i*12) for i in range(5))}
 world=struct.unpack_from('<I',sections[2],4)[0];assert sections[1][:4] in (b'NML1',b'NFM2');models=struct.unpack_from('<I',sections[1],4)[0] if sections[1][:4]==b'NML1' else 1;ids=sections[5];trailer=8+(world+models)*20
 assert ids[trailer:trailer+4]==b'NFB2' and struct.unpack_from('<I',ids,trailer+4)[0]==world+models
 assert struct.unpack_from('<d',ids,trailer+8)[0]==sample['alpha']
 order=struct.unpack_from('<'+str(world+models)+'I',sections[3],8);assert len(sample['commands'])==len(order)
 counts={'road':0,'wall':0,'model':0}
 for command,index in zip(sample['commands'],order):
  kind=3 if command['kind']==5 else command['kind'];position=world+0xffffffff-index if index>=0xfffffff0 else index
  identity=struct.unpack_from('<5I',ids,8+position*20);bounds=struct.unpack_from('<4H',ids,trailer+16+position*8)
  assert identity[0]==kind and identity[2]==int(command['source'],16)
  assert list(bounds)==command['bounds'],(sample['target'],command['index'],bounds,command['bounds'])
  counts[{1:'road',2:'wall',3:'model'}[kind]]+=1
 rows.append(dict(target=sample['target'],alpha=sample['alpha'],exact_command_bounds=True,counts=counts))
report=dict(result='PASS',frames=len(rows),checks=rows,scope='Owned NFB2 bounds and command ordering exactly match independently regenerated native command traces at live fractional targets. Original ARM query/queue parity is separate; raster fidelity and continuous motion unproven.')
out=trace_path.with_name(trace_path.stem+'-packet-bounds-verification.json');out.write_text(json.dumps(report,indent=2));print(json.dumps(dict(result='PASS',frames=len(rows),commands=sum(sum(r['counts'].values()) for r in rows))))

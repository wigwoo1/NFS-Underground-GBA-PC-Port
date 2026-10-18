import csv,json,xml.etree.ElementTree as ET
from pathlib import Path
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/graphics-only-owned-game-20261008')
ns={'e':'http://schemas.microsoft.com/win/2004/08/events'}
root=ET.parse(cp/'dxgkrnl-provider-metadata.xml').getroot()
tasks={n.attrib['value']:n.attrib['name'] for n in root.findall('e:tasks/e:task',ns)}
events={(n.attrib['value'],n.attrib['version']):n.attrib for n in root.findall('e:events/e:event',ns)}
rows=list(csv.DictReader((cp/'owned-pid-events.csv').open(newline='',encoding='utf-8-sig')))
groups={}
for row in rows:
    key=(row['Event ID'],row['Version'])
    meta=events.get(key)
    assert meta is not None, key
    assert meta['task']==row['Task'] and meta['opcode']==row['Opcode'],key
    group=groups.setdefault(key,{'event_id':int(key[0]),'version':int(key[1]),'task':tasks.get(meta['task'],meta['task']),'opcode':int(meta['opcode']),'count':0})
    group['count']+=1
present=[r for r in rows if tasks[events[(r['Event ID'],r['Version'])]['task']]=='Present']
times=sorted(int(r['Clock-Time']) for r in present)
gaps=[(b-a)/10000 for a,b in zip(times,times[1:])]
result={'result':'PASS_LOCAL_METADATA_JOIN','pid':43788,'records':len(rows),'groups':list(groups.values()),'present_event_count':len(present),'present_header_span_ms':(times[-1]-times[0])/10000 if len(times)>1 else None,'present_header_gap_min_ms':min(gaps) if gaps else None,'present_header_gap_max_ms':max(gaps) if gaps else None,'scope':'Local installed provider event/version/task/opcode metadata join. Present event headers do not identify completed display frames; no 60fps or scanout claim.'}
(cp/'owned-event-semantics.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='groups'},indent=2))

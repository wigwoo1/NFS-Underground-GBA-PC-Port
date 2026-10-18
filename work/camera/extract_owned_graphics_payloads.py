import json,collections,xml.etree.ElementTree as ET
from pathlib import Path
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/graphics-only-owned-game-20261008')
ns={'e':'http://schemas.microsoft.com/win/2004/08/events/event'}
# tracerpt uses the standard events/event namespace; verify exact tags before parsing.
records=[]; total=0; schemas=collections.Counter()
for _,event in ET.iterparse(cp/'raw-events.xml',events=('end',)):
    if event.tag.split('}')[-1]!='Event':continue
    uri=event.tag.split('}')[0][1:] if event.tag.startswith('{') else ''
    prefix='{'+uri+'}' if uri else ''
    system=event.find(prefix+'System')
    if system is None:continue
    total+=1
    execution=system.find(prefix+'Execution')
    provider=system.find(prefix+'Provider')
    fields={n.attrib.get('Name',''): (n.text or '').strip() for n in event.findall(prefix+'EventData/'+prefix+'Data')}
    if execution is not None and execution.attrib.get('ProcessID')=='43788':
        eid=system.findtext(prefix+'EventID'); version=system.findtext(prefix+'Version')
        records.append({'provider':provider.attrib.get('Name') if provider is not None else None,'event_id':int(eid),'version':int(version),'time':system.find(prefix+'TimeCreated').attrib['SystemTime'],'tid':execution.attrib.get('ThreadID'),'fields':fields})
        schemas[(int(eid),int(version),tuple(fields))]+=1
    event.clear()
assert total==135543,total
assert len(records)==10955,len(records)
(cp/'owned-event-payloads.json').write_text(json.dumps(records,indent=2))
selected=[r for r in records if r['event_id'] in (184,215,469,470)]
result={'result':'PASS_XML_PAYLOAD_EXTRACTION','total_records':total,'owned_records':len(records),'schemas':[{'event_id':k[0],'version':k[1],'fields':list(k[2]),'count':v} for k,v in schemas.items()],'selected_examples':{str(eid):next(r for r in selected if r['event_id']==eid) for eid in (184,215,469,470)},'scope':'Named payload extraction from existing installed tracerpt decoder, not inferred binary offsets. No completion or display cadence conclusion.'}
(cp/'owned-payload-analysis.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result['selected_examples'],indent=2))

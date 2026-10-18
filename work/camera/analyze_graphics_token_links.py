import json,collections,xml.etree.ElementTree as ET
from pathlib import Path
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/graphics-only-owned-game-20261008')
owned=json.loads((cp/'owned-event-payloads.json').read_text())
starts=[r for r in owned if r['event_id']==215]
assert len(starts)==204
# Integer normalization avoids hex-format differences; zero is never a join key.
def pointer(value):
    try:return int(value,16) if value.lower().startswith('0x') else int(value)
    except (ValueError,AttributeError):return None
tokens=collections.Counter(pointer(r['fields']['Token']) for r in starts)
assert None not in tokens and 0 not in tokens
matches=[];groups=collections.Counter();total=0
for _,event in ET.iterparse(cp/'raw-events.xml',events=('end',)):
    if event.tag.split('}')[-1]!='Event':continue
    uri=event.tag.split('}')[0][1:] if event.tag.startswith('{') else ''
    p='{'+uri+'}' if uri else ''
    system=event.find(p+'System')
    if system is None:continue
    total+=1
    fields={n.attrib.get('Name',''):(n.text or '').strip() for n in event.findall(p+'EventData/'+p+'Data')}
    # Keep field names in evidence; equal pointer values alone do not prove lifecycle semantics.
    hits={k:v for k,v in fields.items() if 'token' in k.lower() and pointer(v) in tokens}
    if hits:
        provider=system.find(p+'Provider').attrib.get('Name','')
        eid=int(system.findtext(p+'EventID'));ver=int(system.findtext(p+'Version'))
        pid=system.find(p+'Execution').attrib['ProcessID']
        record={'provider':provider,'event_id':eid,'version':ver,'pid':int(pid),'time':system.find(p+'TimeCreated').attrib['SystemTime'],'matched_fields':hits,'fields':fields}
        matches.append(record);groups[(provider,eid,ver,int(pid),tuple(hits))]+=1
    event.clear()
assert total==135543
result={'result':'PASS_EXACT_TOKEN_VALUE_SEARCH','starts':len(starts),'unique_tokens':len(tokens),'reused_token_values':sum(n>1 for n in tokens.values()),'matching_records':len(matches),'groups':[{'provider':k[0],'event_id':k[1],'version':k[2],'pid':k[3],'matched_fields':list(k[4]),'count':v} for k,v in groups.items()],'scope':'Exact nonzero token value search across all providers/PIDs. Token recycling, field semantics, trace boundaries and lifecycle ordering require validation before completion/cadence claims.'}
(cp/'token-linked-events.json').write_text(json.dumps(matches,indent=2))
(cp/'token-link-analysis.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))

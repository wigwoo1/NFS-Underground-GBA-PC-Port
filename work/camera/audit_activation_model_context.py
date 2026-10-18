"""Compare source-generated contextual model blocks with original per-draw blocks."""
import runpy,struct,json
from owned_motion_pairs import records
v=runpy.run_path('work/camera/audit_activation_model_assets.py');fixture=v['v'];rom=v['rom'];scene=v['scenes'][1];rows=[r for r in records(fixture['frames'][1])['records'] if r['kind']==3];out=[]
for item in v['results'][1]['items']:
 offset=item['descriptor']-0x08000000;row=next(r for r in rows if bytes(r['blocks'][1])==rom[offset:offset+40])
 source_context=list(item['context']);actual_context=list(struct.unpack('<17I',row['blocks'][0]));sanitized=bytearray(68);raw_context=struct.pack('<17I',*source_context);sanitized[56:60]=raw_context[56:60];sanitized[64:68]=raw_context[64:68];assert bytes(sanitized)==bytes(row['blocks'][0]);projection=list(struct.unpack('<16I',scene.graph.context[304:368]));actual_projection=list(struct.unpack('<16I',row['blocks'][3]))
 palette=bytes(row['blocks'][11]);final_palette=scene.graph.context[384:896];differences=[i for i in range(256) if palette[i*2:i*2+2]!=final_palette[i*2:i*2+2]];used=set(bytes(row['blocks'][10]));affected=sorted(set(differences)&used)
 out.append(dict(palette_differing_indices=differences,texture_affected_indices=affected,object=item['object'],context_differences=[(i,source_context[i],actual_context[i]) for i in range(17) if source_context[i]!=actual_context[i]],projection_differences=[(i,projection[i],actual_projection[i]) for i in range(16) if projection[i]!=actual_projection[i]],rectangle=list(struct.unpack('<4i',row['blocks'][9])),palette_exact=bytes(row['blocks'][11])==scene.graph.context[384:896]))
(fixture['folder']/'activation-model-context.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

"""Replay captured viewport payload through original/candidate bindings and4K."""
import json,runpy,sys
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_camera_scan_candidate import ClosedGraph as Scanner
calls=[0]
def match(self,frame):Scanner.match_frame(self,frame);calls[0]+=1
ClosedGraph.match_frame=match
script=Path('work/camera/test_segmented_original_gpu_parity.py').read_text()
needle="exec(compile(source,'captured_scene_setup','exec'))"
assert script.count(needle)==1
injection="""from owned_closed_viewport import ClosedViewport as ReferenceViewport
from owned_closed_viewport_cache_candidate import ClosedViewport as CachedViewport
viewport_capture=json.loads(Path('work/camera/prototype-runs/viewport-live-binding-1791426419529222400.json').read_text())['checks'][0]
viewport_payload=bytes.fromhex(viewport_capture['viewport_hex'])
viewport_bind_checks=[]
"""
binding=""" address=struct.unpack_from('<I',graph.graph.context,308)[0]
 va=ReferenceViewport(graph.epoch,graph.refresh,graph.graph.refresh,address,viewport_payload)
 vb=CachedViewport(graph.epoch,graph.refresh,graph.graph.refresh,address,viewport_payload)
 ga=va.bind_graph(graph);gb=vb.bind_graph(graph)
 assert ga==gb and ga.graph.validate()==gb.graph.validate()
 viewport_bind_checks.append(dict(epoch=graph.epoch,refresh=graph.refresh,viewport_hex=viewport_payload.hex()))
 graph=gb
 scenes.append("""
replacement="source="+repr(injection)+"+source.replace(' scenes.append(',"+repr(binding)+")\n"+needle
script=script.replace(needle,replacement)
exec(compile(script,'combined_viewport_gpu_replay','exec'))
assert calls[0]>0 and len(viewport_bind_checks)==2
p=Path(sys.argv[2]);r=json.loads(p.read_text());r['camera_scanner_calls']=calls[0];r['viewport_bind_checks']=viewport_bind_checks;r['viewport_scope']='Live-captured16-byte viewport payload rebound to fixture identities/addresses; paired original/candidate input fields exact. This is a replay, not original viewport capture at fixture time.';p.write_text(json.dumps(r,indent=2));print('PASS',calls[0],'scanner calls and',len(viewport_bind_checks),'paired viewport bindings')

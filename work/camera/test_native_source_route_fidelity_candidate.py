import sys,json,pickle
from pathlib import Path
from owned_scene_process_transport import unpack
from owned_native_source_process_preparation_candidate import ProcessPreparationService
import owned_world_preparation_service as direct_module
from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
from test_scene_process_transport import digest

def main():
 folder=Path(sys.argv[1]);manifest=json.loads((folder/'manifest.json').read_text())
 rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
 direct_module.PrecomputedWorldSamples=PrecomputedSourceWorldSamples
 direct=direct_module.WorldPreparationService(rom,2);shared='--shared-output' in sys.argv;child=ProcessPreparationService(rom,2,shared_output=shared)
 previous=None;checks=[]
 try:
  for row in manifest['rows']:
   packets=pickle.loads((folder/row['file']).read_bytes());older=unpack(packets[0],rom);newer=unpack(packets[1],rom)
   if previous is not None:
    assert older[1].identity==previous[1].identity,'Nonconsecutive capture'
    older=previous
   alphas=tuple(row['alphas'])
   a=direct.take(direct.submit(older,newer,alphas,timeout=30));b=child.take(child.submit(older,newer,alphas,timeout=30))
   try:
    assert getattr(a,'history_only',False)==b.history_only
    if alphas:
     assert a.source_cameras==b.source_cameras
     for alpha in alphas:
      assert digest(a.sample(alpha))==digest(b.sample(alpha)),(row['older'],alpha)
      x=a.source_masks[alpha];y=b.source_masks[alpha]
      assert bytes(x[0])==bytes(y[0]) and bytes(x[1])==bytes(y[1]) and x[2:]==y[2:]
    checks.append(dict(older=row['older'],newer=row['newer'],samples=len(alphas)))
   finally:a.close();b.close()
   previous=newer
 finally:direct.close();child.close()
 if shared:assert child.shutdown_evidence['shared_mapping_closed']
 assert len(checks)>=2
 assert all(x['input_reused'] for x in child.stage_samples[1:])
 assert child.shutdown_evidence['child_exitcode']==0 and not child.shutdown_evidence['forced_termination']
 result=dict(result='PASS_CONSECUTIVE_NATIVE_SOURCE_FIDELITY',checks=checks,shared_output=shared,shutdown=child.shutdown_evidence,scope='Bounded captured route through independently retained direct/child histories; exact source data parity, not pixel or cadence certification.')
 (folder/('fidelity-shared.json' if shared else 'fidelity.json')).write_text(json.dumps(result,indent=2));print(result['result'],len(checks),sum(x['samples'] for x in checks))
if __name__=='__main__':main()


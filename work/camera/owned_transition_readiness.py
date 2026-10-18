"""Load transition code before admitting the original live game clock."""
import importlib,time
MODULES=('owned_external_model_owners','owned_scenery_record_pairs','owned_scenery_motion','owned_external_record_pair','owned_removed_scenery_visit')
def prepare():
 started=time.perf_counter_ns()
 for name in MODULES:importlib.import_module(name)
 return dict(modules=list(MODULES),wall_ns=time.perf_counter_ns()-started,scope='Code import readiness only; no scene-specific model preparation or game updates')

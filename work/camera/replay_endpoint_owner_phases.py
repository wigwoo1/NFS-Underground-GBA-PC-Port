import runpy,sys
from owned_endpoint_owner_phases import install
install()
if '--preimport-external' in sys.argv:
 import owned_external_model_owners
runpy.run_path('work/camera/replay_exact_pair_stage_trace.py',run_name='__main__')


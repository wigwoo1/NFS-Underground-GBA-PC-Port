import runpy
import owned_wall_visibility_phases as phases
import owned_wall_visibility_timed as native
phases.namespace['helper']=lambda:native.helper
phases.namespace['batch_types']=phases.original.batch_types
phases.namespace['table']=phases.original.table
phases.install()
runpy.run_path('work/camera/test_combined_segmented_gpu.py',run_name='__main__')
assert len(native.records)==len(phases.records)>0
print('PASS timed visibility coverage',len(native.records))

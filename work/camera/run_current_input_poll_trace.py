import os,runpy
assert os.environ.get('NFSUG_INPUT_POLL_TRACE')=='1'
try:runpy.run_path('work/camera/run_native_sky_reader_bulk.py',run_name='__main__')
finally:
 from owned_input_poll_ledger_candidate import save
 save('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/current-input-poll-ledger.json')

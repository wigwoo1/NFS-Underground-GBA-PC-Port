"""Visible-window verification of unchanged default playable renderer."""
import runpy,sys
# Keep original renderer and timing; visibility is required for cadence tests.
if '--show-smoke-window' not in sys.argv:sys.argv.append('--show-smoke-window')
# A verification run must retain every original update for the deadline audit.
if '--capture-update-profile' not in sys.argv:sys.argv.append('--capture-update-profile')
runpy.run_path('work/camera/run_native_batch_compact_all_diagnostics.py',run_name='__main__')

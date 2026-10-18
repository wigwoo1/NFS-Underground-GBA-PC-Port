"""Optional exact shared-section reuse, explicitly enabled after startup environment reset."""
import sys,runpy
if "--shared-output-dedup" not in sys.argv:sys.argv.append("--shared-output-dedup")
runpy.run_path("work/camera/run_process_frame_reuse_candidate.py",run_name="__main__")

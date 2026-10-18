"""Rebuild the maintained optimized PC preview and all required verification."""
from pathlib import Path
import argparse,subprocess,sys
here=Path(__file__).resolve().parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-maintained-integration')
p=argparse.ArgumentParser();p.add_argument('--print-steps',action='store_true');options=p.parse_args()
steps=[['build_source_frame.py'],['test_source_reader.py'],['test_source_reader_direct.py'],['build_source_scene.py'],['build_source_transfer_core.py','--reuse'],['test_source_transfer_core.py'],['build_live_host.py','--reuse-scene','--source-transfer-core','--output-dir',str(out)],['test_live_host.py','--output-dir',str(out),'--direct-cached'],['test_logic_audit.py','--output-dir',str(out),'--direct-cached'],['package_source_transfer_host.py']]
for step in steps:
 print(' '.join(step),flush=True)
 if not options.print_steps:subprocess.run([sys.executable,str(here/step[0]),*step[1:]],check=True)

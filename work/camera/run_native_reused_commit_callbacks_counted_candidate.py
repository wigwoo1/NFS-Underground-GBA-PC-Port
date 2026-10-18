from pathlib import Path
path=Path('work/camera/run_native_ordered_tail_candidate.py');source=path.read_text()
source=source.replace("try:exec(","import owned_commit_callback_reuse_install_candidate\ntry:exec(")
try:exec(compile(source,str(path),'exec'),dict(__name__='__main__',__file__=str(path)))
finally:
 import json,owned_commit_callback_reuse_install_candidate as profile
 assert profile.stats['active']==0
 Path('work/camera/prototype-runs/reused-callback-activation-20261009.json').write_text(json.dumps(profile.stats,indent=2));print('REUSED_CALLBACK_ACTIVATION',profile.stats)

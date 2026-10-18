from pathlib import Path
path=Path('work/camera/run_native_ordered_tail_candidate.py');source=path.read_text()
source=source.replace("try:exec(","import owned_commit_callback_reuse_install_candidate\ntry:exec(")
exec(compile(source,str(path),'exec'),dict(__name__='__main__',__file__=str(path)))

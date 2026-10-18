from pathlib import Path
path=Path('work/camera/test_ordered_tail_pair_4k_candidate.py');source=path.read_text()
source=source.replace('source=path.read_text()',"source=path.read_text()\nsource=source.replace('import owned_d3d_call_profile_install_candidate\\n','import owned_d3d_call_profile_install_candidate\\nimport owned_acyclic_byte_owner_install_candidate\\n')")
source=source.replace('ordered-tail-pair-4k-','acyclic-owner-pair-4k-')
exec(compile(source,str(path),'exec'),dict(__name__='__main__',__file__=str(path)))

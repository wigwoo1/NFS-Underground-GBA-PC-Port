import sys
from pathlib import Path
path=Path('work/camera/test_prepared_pair_4k_candidate.py')
source=path.read_text()
source=source.replace('import owned_d3d_call_profile_install_candidate\n','import owned_d3d_call_profile_install_candidate\nimport owned_ordered_render_tail_install_candidate\n')
source=source.replace("prepared-pair-4k-","ordered-tail-pair-4k-")
exec(compile(source,str(path),'exec'),dict(__name__='__main__',__file__=str(path)))


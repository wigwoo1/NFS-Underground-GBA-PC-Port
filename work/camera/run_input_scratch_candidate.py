import sys
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'work/camera'))
source=(root/'work/camera/run_prepared_hud_packaged.py').read_text()
marker=r' install_fused()\\n';assert source.count(marker)==1
source=source.replace(marker,marker+r' import owned_input_scratch_candidate\\n')
exec(compile(source,str(root/'work/camera/run_prepared_hud_packaged.py'),'exec'),dict(__name__='__main__',__file__=str(root/'work/camera/run_prepared_hud_packaged.py')))


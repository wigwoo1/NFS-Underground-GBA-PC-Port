import sys,runpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import owned_native_source_texture_backdrop_session_candidate as session
from owned_source_d3d_texture_backdrop_consumer_memcmp_candidate import OwnedD3DConsumer
session.OwnedD3DConsumer=OwnedD3DConsumer
root=Path(r'G:\EXTRA DATA DRIVE\Desktop\Games\Codex\NFSUG-Native-PC-Port')
source_report=root/'work'/'camera'/'prototype-runs'/'owned-native-1791681495180833500.json'
output=root/'work'/'camera'/'prototype-runs'/'d3d-memcmp-source-parity.json'
sys.argv=[str(root/'work'/'camera'/'test_owned_native_source_texture_backdrop_parity_candidate.py'),str(source_report),str(output)]
runpy.run_path(str(sys.argv[0]),run_name='__main__')
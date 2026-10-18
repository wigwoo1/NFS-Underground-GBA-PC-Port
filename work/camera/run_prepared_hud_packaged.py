import pathlib,sys,runpy
root=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'work/camera'))
import owned_fine_deadline_trace
original=runpy.run_path
injected=False
def run(path,*args,**kwargs):
 global injected
 if pathlib.Path(path).name=='run_native_long_sky_linear_candidate.py':
  source=pathlib.Path(path).read_text();marker='import owned_hud_borrowed_rows_install_candidate\\n';assert source.count(marker)==1
  source=source.replace(marker,marker+' from owned_prepared_hud_live_install import install as install_fused\\n install_fused()\\n');injected=True
  return exec(compile(source,str(path),'exec'),dict(__name__='__main__',__file__=str(path)))
 return original(path,*args,**kwargs)
runpy.run_path=run
try:original(str(root/'work/camera/run_native_endpoint_profile_candidate.py'),run_name='__main__')
finally:runpy.run_path=original
assert injected





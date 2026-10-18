from pathlib import Path
p=Path('work/camera');s=(p/'run_owned_native_prototype.py').read_text();old='32 if 80<=len(inputs)<400 else 16 if 400<=len(inputs)<600 else 0';assert s.count(old)==1
(p/'run_owned_gentle_sky_diagnostic.py').write_text(s.replace(old,'32 if 80<=len(inputs)<92 else 16 if 140<=len(inputs)<152 else 0'))
r=(p/'run_source_sky_pixels_candidate.py').read_text();r=r.replace("runpy.run_path('work/camera/run_source_compact_diagnostics_candidate.py',run_name='__main__')",'''original_run_path=runpy.run_path
def redirect(path,*args,**kwargs):
 if path=='work/camera/run_owned_native_prototype.py':path='work/camera/run_owned_gentle_sky_diagnostic.py'
 return original_run_path(path,*args,**kwargs)
runpy.run_path=redirect
runpy.run_path('work/camera/run_source_compact_diagnostics_candidate.py',run_name='__main__')''');(p/'run_gentle_sky_pixels_candidate.py').write_text(r)

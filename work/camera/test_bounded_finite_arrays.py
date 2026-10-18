import ctypes as C,math,json
from pathlib import Path
from owned_native_presentation_batch import finite_array,_finite
checks=[]
for n in (0,12,216,4096,4097):
 values=[float(i) for i in range(n)];a=(C.c_double*n)(*values)
 assert finite_array(a)==bool(_finite(a,n))==True
 checks.append(dict(length=n,finite=True))
 if n:
  for value in (math.nan,math.inf,-math.inf):
   a[n-1]=value;assert finite_array(a)==bool(_finite(a,n))==False
  checks.append(dict(length=n,nonfinite_rejected=True))
assert finite_array([1.,2.]) and not finite_array([math.nan])
Path('work/camera/bounded-finite-tests.json').write_text(json.dumps(dict(result='PASS',checks=checks),indent=2));print('PASS bounded finite scan thresholds and malformed values')

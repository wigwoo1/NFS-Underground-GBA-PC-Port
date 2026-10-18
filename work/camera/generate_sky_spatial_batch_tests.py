from pathlib import Path
p=Path('work/camera')
for name,cp in [('test_sky_spatial_wraps.py','sky-spatial-wraps-20261007'),('test_sky_spatial_candidate.py','sky-spatial-candidate-20261007'),('benchmark_sky_spatial_draw.py','sky-spatial-draw-cost-20261007')]:
 new=name.replace('sky_spatial','sky_spatial_batch')
 s=(p/name).read_text().replace('owned-sky-spatial-diagnostic.dll','owned-sky-spatial-batch.dll').replace(cp,cp.replace('sky-spatial','sky-spatial-batch')).replace(name,new)
 (p/new).write_text(s)

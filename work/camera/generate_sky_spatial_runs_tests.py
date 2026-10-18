from pathlib import Path
p=Path('work/camera')
for name in ('test_sky_spatial_batch_wraps.py','test_sky_spatial_batch_candidate.py','benchmark_sky_spatial_batch_draw.py'):
 new=name.replace('spatial_batch','spatial_runs');s=(p/name).read_text().replace('owned-sky-spatial-batch.dll','owned-sky-spatial-runs.dll').replace('sky-spatial-batch','sky-spatial-runs').replace(name,new)
 if 'candidate' in name:s=s.replace('cell_columns=len(cols),','cell_columns=len(cols),vertices=d.nf_sky_spatial_vertex_count(),')
 (p/new).write_text(s)

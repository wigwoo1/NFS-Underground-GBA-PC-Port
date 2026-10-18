"""Generate isolated bounded GPU-owner sky vertex allocation reuse."""
from pathlib import Path
p=Path('work/camera');s=(p/'owned_gpu_segmented_source_candidate.c').read_text()
a='static unsigned sky_spatial_vertex_count;';assert s.count(a)==1
s=s.replace(a,a+'\nstatic void*sky_vertex_storage;static size_t sky_vertex_bytes;static uint64_t sky_vertex_allocations;')
a='SkySpatialVertex*vertices=malloc(sizeof(*vertices)*vertex_count);if(!vertices)return 26;';assert s.count(a)==1
s=s.replace(a,'if(!sky_vertex_storage){sky_vertex_storage=malloc(sizeof(SkySpatialVertex)*vertex_count);if(!sky_vertex_storage)return 26;sky_vertex_bytes=sizeof(SkySpatialVertex)*vertex_count;sky_vertex_allocations++;}\n SkySpatialVertex*vertices=sky_vertex_storage;')
a='glPopClientAttrib();free(vertices);';assert s.count(a)==1;s=s.replace(a,'glPopClientAttrib();')
a='owned_pool_clear();preview_shutdown();';assert s.count(a)==2
s=s.replace(a,'owned_pool_clear();free(sky_vertex_storage);sky_vertex_storage=NULL;sky_vertex_bytes=0;preview_shutdown();')
s+='\n__declspec(dllexport) int nf_sky_vertex_buffer_stats(uint64_t*out){if(!out)return 0;out[0]=sky_vertex_bytes;out[1]=sky_vertex_allocations;return 1;}\n'
(p/'owned_gpu_segmented_sky_buffer_candidate.c').write_text(s)


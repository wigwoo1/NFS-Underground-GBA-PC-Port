from pathlib import Path
p=Path('work/camera/owned_hud_gpu.h');s=p.read_text().replace('#include "layer_snapshot.h"','#include "layer_snapshot.h"\n#include "hud_row_pool.h"');s=s.replace('static int owned_hud_gpu_draw(const void*data,size_t size,const uint8_t*text_indices_data,const uint8_t*text_coverage_data){','static int owned_hud_gpu_draw_rows(const void*data,size_t size,const NFHudRowPool*pool,const uint8_t*text_indices_data,const uint8_t*text_coverage_data){');needle=' uint32_t hud_refresh;memcpy(&hud_refresh,data,4);';assert needle in s;s=s.replace(needle,' if(pool&&!nf_hud_pool_valid(pool,pool->bytes,pool->epoch))return 0;\n'+needle);s=s.replace('memcpy(&check,(const uint8_t*)data+y*sizeof(check),sizeof(check));','if(pool){if(!nf_hud_pool_row(pool,pool->bytes,pool->epoch,y,&check))return 0;}else memcpy(&check,(const uint8_t*)data+y*sizeof(check),sizeof(check));');s=s.replace('  memcpy(&row,(const uint8_t*)data+y*sizeof(row),sizeof(row));','  if(pool){if(!nf_hud_pool_row(pool,pool->bytes,pool->epoch,y,&row)){ok=0;break;}}else memcpy(&row,(const uint8_t*)data+y*sizeof(row),sizeof(row));');s=s.replace('\n#endif','''
static unsigned hud_pool_draws,hud_pool_verified_rows;
static uint64_t hud_pool_full_bytes,hud_pool_stored_bytes;
static int owned_hud_gpu_draw(const void*data,size_t size,const uint8_t*indices,const uint8_t*coverage){
 if(!getenv("NF_TEST_HUD_ROW_POOL"))return owned_hud_gpu_draw_rows(data,size,NULL,indices,coverage);
 NFHudRowPool*pool=nf_hud_pool_create(data,size,1);if(!pool)return 0;
 int ok=nf_hud_pool_valid(pool,pool->bytes,1);
 /* Diagnostic independent full-row reference before GPU consumes pooled rows. */
 if(ok&&getenv("NF_VERIFY_HUD_ROW_POOL")){for(unsigned y=0;y<160;y++){NFHudLayerRow row;if(!nf_hud_pool_row(pool,pool->bytes,1,y,&row)||memcmp(&row,(const uint8_t*)data+y*sizeof(row),sizeof(row))){ok=0;break;}hud_pool_verified_rows++;}}
 if(ok)ok=owned_hud_gpu_draw_rows(data,size,pool,indices,coverage);
 if(ok){hud_pool_draws++;hud_pool_full_bytes+=size;hud_pool_stored_bytes+=pool->bytes;}free(pool);return ok;
}
#endif''');p.write_text(s)
p=Path('work/camera/threaded_preview.c');s=p.read_text();s=s.replace('if(components)fclose(components);if(stages)fclose(stages);','printf("hud_pool_draws=%u hud_pool_verified_rows=%u hud_pool_full_bytes=%llu hud_pool_stored_bytes=%llu\\n",hud_pool_draws,hud_pool_verified_rows,(unsigned long long)hud_pool_full_bytes,(unsigned long long)hud_pool_stored_bytes);if(components)fclose(components);if(stages)fclose(stages);',1);p.write_text(s)
p=Path('work/camera/audit_threaded_racing_motion.py');s=p.read_text().replace("for flag in ['NF_TEST_GPU_TIMESTAMPS'","for flag in ['NF_TEST_HUD_ROW_POOL','NF_VERIFY_HUD_ROW_POOL','NF_TEST_GPU_TIMESTAMPS'");needle='rate=16777216/(280896*60)';s=s.replace(needle,"if os.environ.get('NF_TEST_HUD_ROW_POOL')=='1':\n assert stats['hud_pool_draws']>0 and stats['hud_pool_stored_bytes']>0\n if os.environ.get('NF_VERIFY_HUD_ROW_POOL')=='1':assert stats['hud_pool_verified_rows']==160*stats['hud_pool_draws']\n"+needle,1);p.write_text(s)

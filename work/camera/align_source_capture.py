from pathlib import Path
p=Path('work/camera/world_trace.h');s=p.read_text()
s=s.replace('static uint8_t*owned_current_sources;static size_t owned_current_sources_bytes;','static uint8_t*owned_current_sources,*owned_source_pending;static size_t owned_current_sources_bytes,owned_source_pending_bytes;')
s=s.replace('static void owned_builder_reset(void){free(owned_current_sources);','static void owned_builder_reset(void){free(owned_source_pending);owned_source_pending=NULL;owned_source_pending_bytes=0;free(owned_current_sources);')
s=s.replace('This is a separately timed diagnostic packet, not a graph-source pose.','Captured at graph source boundary; copied atomically at scene publication.')
s=s.replace('uint32_t h[6]={0x31534f4e,1,refresh,c->frameCounter(c),count,168};','uint32_t h[6]={0x31534f4e,2,refresh,c->frameCounter(c),count,168};')
s=s.replace('free(owned_current_sources);owned_current_sources=data;owned_current_sources_bytes=n;return 1;','free(owned_source_pending);owned_source_pending=data;owned_source_pending_bytes=n;return 1;')
s=s.replace('if(!owned_current_sources_capture(epoch,refresh))return;','if(!owned_source_pending)return;unsigned captured;memcpy(&captured,owned_source_pending+12,4);if(captured!=source)return;uint8_t*source_copy=malloc(owned_source_pending_bytes);if(!source_copy)return;memcpy(source_copy,owned_source_pending,owned_source_pending_bytes);memcpy(source_copy+8,&refresh,4);free(owned_current_sources);owned_current_sources=source_copy;owned_current_sources_bytes=owned_source_pending_bytes;')
needle='if(owned_graph_live_enabled){free(owned_graph_live_data);'
assert needle in s;s=s.replace(needle,'if(owned_graph_live_enabled&&complete&&!owned_current_sources_capture(owned_graph_build_epoch,c->frameCounter(c)))complete=0;'+needle)
p.write_text(s)
p=Path('work/camera/run_owned_native_prototype.py');s=p.read_text().replace('ch[:3]==(0x31534f4e,1,candidate)','ch[:3]==(0x31534f4e,2,candidate) and ch[3]==graph.graph.refresh');p.write_text(s)

package org.codex.nfsugpreview;
/** Optional wall-time accounting. Capture metrics publish only at outer completion. */
final class NativeWorkProfile {
 static final int STEP=0,LEGACY=1,AUDIO=2,CAPTURE=3,PREPARE=4,BACKGROUND=5,ROAD=6,WALL=7,WORLD=8,HUD=9,DRAW=10,INIT=11,CAPTURE_BG_COPY=12,CAPTURE_BG_BIND=13,CAPTURE_WORLD_COPY=14,CAPTURE_BG_PARSE=15,CAPTURE_HISTORY_COPY=16,CAPTURE_HISTORY_PARSE=17,CAPTURE_ROAD_RETAIN=18,CAPTURE_WALL_RETAIN=19,CAPTURE_PREPARED=20;
 static final String[] NAMES={"core_step","legacy_snapshot","audio_offer","complete_capture","draw_prepare","background_dispatch","road_dispatch","wall_dispatch","world_dispatch","hud_dispatch","native_draw","gpu_objects_init","capture_background_copy","capture_background_bind_inclusive","capture_world_copy_nested_in_bind","capture_background_parse_or_reuse","capture_history_copy","capture_history_parse","capture_road_retention","capture_wall_retention","capture_prepared_constructor"};
 static long start(NativeWorkProfile p){return p==null?0:p.start();}
 static void end(NativeWorkProfile p,int stage,long start){if(p!=null)p.end(stage,start);}
 volatile boolean enabled;
 private final long[][] values=new long[NAMES.length][3];
 private final ThreadLocal<long[][]> capture=new ThreadLocal<>();
 long start(){return enabled?System.nanoTime():0;}
 private static void record(long[] row,long elapsed){row[0]++;row[1]+=elapsed;row[2]=Math.max(row[2],elapsed);}
 void end(int stage,long start){
  if(start==0)return;long elapsed=System.nanoTime()-start;
  if(stage>=CAPTURE_BG_COPY){long[][] pending=capture.get();if(pending!=null){record(pending[stage],elapsed);return;}}
  synchronized(this){record(values[stage],elapsed);}
 }
 /** Enable profiling before starting the worker; normal disabled captures allocate nothing. */
 long captureStart(){
  long start=start();if(start==0)return 0;
  if(capture.get()!=null)throw new IllegalStateException("Capture profile already active");
  capture.set(new long[NAMES.length][3]);return start;
 }
 /** Called in finally: exceptions and null results remain measured completed attempts. */
 void captureEnd(long start){
  if(start==0)return;long elapsed=System.nanoTime()-start;long[][] pending=capture.get();
  if(pending==null)throw new IllegalStateException("Capture profile not active");
  capture.remove();record(pending[CAPTURE],elapsed);
  synchronized(this){for(int stage=0;stage<values.length;stage++){
   values[stage][0]+=pending[stage][0];values[stage][1]+=pending[stage][1];values[stage][2]=Math.max(values[stage][2],pending[stage][2]);
  }}
 }
 synchronized long[] stage(int stage){return values[stage].clone();}
 /** One reporting instant; unfinished capture batches are absent from all stages. */
 synchronized long[][] snapshot(){long[][] result=new long[values.length][];for(int i=0;i<values.length;i++)result[i]=values[i].clone();return result;}
}

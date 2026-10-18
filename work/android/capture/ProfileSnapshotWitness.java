package org.codex.nfsugpreview;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicReference;
/** Diagnostic only: exercises unchanged production counters with controlled scheduling. */
public final class ProfileSnapshotWitness {
 static void ok(boolean condition,String message){if(!condition)throw new AssertionError(message);}
 static void waitFor(CountDownLatch latch)throws Exception{ok(latch.await(5,TimeUnit.SECONDS),"Worker barrier timed out");}
 static void capture(NativeWorkProfile p){long outer=p.start();long inner=p.start();p.end(NativeWorkProfile.CAPTURE_BG_COPY,inner);p.end(NativeWorkProfile.CAPTURE,outer);}
 static void balanced(NativeWorkProfile p,int expected){ok(p.stage(NativeWorkProfile.CAPTURE)[0]==expected,"Wrong outer count");ok(p.stage(NativeWorkProfile.CAPTURE_BG_COPY)[0]==expected,"Wrong nested count");}
 static void mixedReads()throws Exception{
  NativeWorkProfile p=new NativeWorkProfile();p.enabled=true;capture(p);balanced(p,1);
  long reportedOuter=p.stage(NativeWorkProfile.CAPTURE)[0];
  CountDownLatch begin=new CountDownLatch(1),done=new CountDownLatch(1);
  AtomicReference<Throwable> failure=new AtomicReference<>();
  Thread worker=new Thread(()->{try{waitFor(begin);capture(p);}catch(Throwable t){failure.set(t);}finally{done.countDown();}},"finished-between-stage-reads");
  worker.start();begin.countDown();waitFor(done);worker.join(5000);ok(!worker.isAlive(),"Worker still live");
  ok(failure.get()==null,"Worker failed: "+failure.get());
  long reportedNested=p.stage(NativeWorkProfile.CAPTURE_BG_COPY)[0];
  ok(reportedOuter==1&&reportedNested==2,"Did not reproduce mixed completed samples");balanced(p,2);
 }
 static void inFlight()throws Exception{
  NativeWorkProfile p=new NativeWorkProfile();p.enabled=true;capture(p);balanced(p,1);
  CountDownLatch nestedFinished=new CountDownLatch(1),releaseOuter=new CountDownLatch(1),done=new CountDownLatch(1);
  AtomicReference<Throwable> failure=new AtomicReference<>();
  Thread worker=new Thread(()->{try{
   long outer=p.start();long inner=p.start();p.end(NativeWorkProfile.CAPTURE_BG_COPY,inner);nestedFinished.countDown();waitFor(releaseOuter);p.end(NativeWorkProfile.CAPTURE,outer);
  }catch(Throwable t){failure.set(t);}finally{nestedFinished.countDown();done.countDown();}},"nested-finished-outer-inflight");
  worker.start();
  try{waitFor(nestedFinished);ok(failure.get()==null,"Worker failed");
   // No writes can happen here until releaseOuter. Even an atomic copy of all
   // metrics would retain this imbalance; completed-work accounting is needed.
   ok(p.stage(NativeWorkProfile.CAPTURE)[0]==1&&p.stage(NativeWorkProfile.CAPTURE_BG_COPY)[0]==2,"Did not reproduce inflight nesting");
  }finally{releaseOuter.countDown();waitFor(done);worker.join(5000);}
  ok(!worker.isAlive()&&failure.get()==null,"Worker failed to finish");balanced(p,2);
 }
 public static void main(String[] args)throws Exception{
  for(int i=0;i<200;i++){mixedReads();inFlight();}
  System.out.println("{\"result\":\"PASS_UNCHANGED_PROFILE_SNAPSHOT_WITNESS\",\"mixed_completed_read_cases\":200,\"inflight_nested_cases\":200,\"quiescent_counts_balanced\":true,\"production_code_modified\":false,\"android_runtime_test\":false}");
 }
}

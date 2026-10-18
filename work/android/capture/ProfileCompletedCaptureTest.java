package org.codex.nfsugpreview;
import java.util.concurrent.*;import java.util.concurrent.atomic.AtomicReference;
public final class ProfileCompletedCaptureTest {
 static void ok(boolean b,String why){if(!b)throw new AssertionError(why);}
 static void await(CountDownLatch latch)throws Exception{ok(latch.await(5,TimeUnit.SECONDS),"Barrier timed out");}
 static void balanced(long[][] s,int expected){ok(s[NativeWorkProfile.CAPTURE][0]==expected,"Outer cohort");ok(s[NativeWorkProfile.CAPTURE_BG_COPY][0]==expected,"Nested cohort");ok(s[NativeWorkProfile.CAPTURE_BG_COPY][1]<=s[NativeWorkProfile.CAPTURE][1],"Nested exceeds outer duration");}
 static void capture(NativeWorkProfile p){long outer=p.captureStart();try{long child=p.start();p.end(NativeWorkProfile.CAPTURE_BG_COPY,child);}finally{p.captureEnd(outer);}}
 static void interleaved()throws Exception{
  NativeWorkProfile p=new NativeWorkProfile();p.enabled=true;capture(p);balanced(p.snapshot(),1);long[][] first=p.snapshot();
  CountDownLatch childDone=new CountDownLatch(1),finish=new CountDownLatch(1),done=new CountDownLatch(1);AtomicReference<Throwable> failure=new AtomicReference<>();
  Thread worker=new Thread(()->{long outer=p.captureStart();try{long inner=p.start();p.end(NativeWorkProfile.CAPTURE_BG_COPY,inner);childDone.countDown();await(finish);}catch(Throwable t){failure.set(t);}finally{p.captureEnd(outer);done.countDown();}},"completed-capture-test");
  worker.start();try{await(childDone);balanced(p.snapshot(),1);balanced(first,1);
   long draw=p.start();p.end(NativeWorkProfile.DRAW,draw);ok(p.snapshot()[NativeWorkProfile.DRAW][0]==1,"Other thread stage missing");
  }finally{finish.countDown();await(done);worker.join(5000);}
  ok(!worker.isAlive()&&failure.get()==null,"Worker failure: "+failure.get());balanced(p.snapshot(),2);balanced(first,1);
  first[NativeWorkProfile.CAPTURE][0]=99;balanced(p.snapshot(),2);
 }
 public static void main(String[] args)throws Exception{
  for(int i=0;i<200;i++)interleaved();
  NativeWorkProfile p=new NativeWorkProfile();capture(p);balanced(p.snapshot(),0);p.enabled=true;
  long outer=p.captureStart();try{long child=p.start();p.end(NativeWorkProfile.CAPTURE_BG_COPY,child);throw new IllegalArgumentException("expected");}catch(IllegalArgumentException expected){}finally{p.captureEnd(outer);}balanced(p.snapshot(),1);
  outer=p.captureStart();boolean rejected=false;try{p.captureStart();}catch(IllegalStateException expected){rejected=true;}finally{p.captureEnd(outer);}ok(rejected,"Nested scope accepted");
  ok(p.snapshot()[NativeWorkProfile.CAPTURE][0]==2,"Finally attempt count");capture(p);long[][] finalCounts=p.snapshot();ok(finalCounts[NativeWorkProfile.CAPTURE][0]==3&&finalCounts[NativeWorkProfile.CAPTURE_BG_COPY][0]==2,"Empty attempts and scope cleanup");
  System.out.println("{\"result\":\"PASS_COMPLETED_CAPTURE_PROFILE\",\"interleaved_cases\":200,\"inflight_batch_hidden\":true,\"snapshot_independent\":true,\"exception_finally_measured\":true,\"disabled_no_counters\":true,\"other_thread_stages_preserved\":true}");
 }
}

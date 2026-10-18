package org.codex.nfsugpreview;
import java.util.*;
/** Original 03003190: wrapping 32-bit perspective-to-affine run planning. */
final class NativeRoadPerspective {
 static final class Plan{final int[][] runs;final int[] end;Plan(int[][] r,int[] e){runs=r;end=e;}}
 private static int[] unproject(int q,int u,int v,int[] reciprocal){int at=q>>4;if(at<0||at>=32768)throw new IllegalArgumentException("Road reciprocal index");return new int[]{(reciprocal[at]*(u>>8))>>4,(reciprocal[at]*(v>>8))>>4};}
 static Plan plan(int[] params,int[] reciprocal,int capacity){
  if(params==null||params.length!=16||reciprocal==null||reciprocal.length!=32768||Integer.toUnsignedLong(params[7])>512||capacity<0)throw new IllegalArgumentException("Road perspective inputs");
  int[] c=params.clone();int remaining=c[7],q=c[10],u=c[8],v=c[9];
  int dq=(int)(((long)(c[13]-q)*(long)c[4])>>>12);
  int du=(((c[11]-u)>>8)*c[4])>>4,dv=(((c[12]-v)>>8)*c[4])>>4;
  int[] a=unproject(q,u,v,reciprocal);c[7]=16;ArrayList<int[]> runs=new ArrayList<int[]>();
  while(remaining!=0){q+=dq;u+=du;v+=dv;int[] next=unproject(q,u,v,reciprocal);c[8]=a[0]+c[14];c[9]=a[1]+c[15];c[10]=(next[0]-a[0])>>4;c[11]=(next[1]-a[1])>>4;if(remaining<=15)c[7]=remaining;runs.add(c.clone());c[6]+=32;a=next;remaining=remaining>16?remaining-16:0;}
  if(runs.size()>capacity)throw new IllegalArgumentException("Road run capacity");return new Plan(runs.toArray(new int[runs.size()][]),c.clone());
 }
}

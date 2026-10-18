package org.codex.nfsugpreview;
/** Preflight every retained owner before drawing; top/bottom ownership is source-derived. */
final class NativeSceneComposition {
 private final NativeSceneSnapshot source;private final NativeSceneDrawPlan[] plans;private final int cut;
 NativeSceneComposition(NativeSceneSnapshot scene){if(scene==null)throw new IllegalArgumentException("Owned scene required");source=scene;plans=new NativeSceneDrawPlan[scene.geometryCount()];for(int i=0;i<plans.length;i++)plans[i]=new NativeSceneDrawPlan(scene.geometry(i));cut=scene.splitRow;}
 boolean belongsTo(NativeSceneSnapshot scene){return source==scene;}
 int count(){return plans.length;}NativeSceneDrawPlan plan(int owner){return plans[owner];}
 NativeDrawBounds clip(int owner,NativeDrawBounds bounds){return intersect(bounds,owner==0?0:cut,plans.length==1||owner==1?160:cut);}
 static NativeDrawBounds intersect(NativeDrawBounds b,int top,int bottom){if(top<0||bottom>160||top>bottom)throw new IllegalArgumentException("Owner rows");int t=Math.max(top,b.top),end=Math.min(bottom,b.bottom);return new NativeDrawBounds(b.left,b.right,t,Math.max(t,end));}
}

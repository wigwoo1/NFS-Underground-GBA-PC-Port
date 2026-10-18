package org.codex.nfsugpreview;
/** Immutable owner-thread capture for render-thread handoff. No core pointers. */
final class NativeRetainedScene {
 final NativePreparedScene prepared;final NativeBackgroundScene background;final NativeRoadRetention roads;final NativeWallRetention walls;final long epoch,refresh;
 private NativeRetainedScene(NativeBackgroundScene b,NativeRoadRetention r,NativeWallRetention w,NativeWorkProfile profile){long start=NativeWorkProfile.start(profile);prepared=new NativePreparedScene(b);NativeWorkProfile.end(profile,NativeWorkProfile.CAPTURE_PREPARED,start);background=b;roads=r;walls=w;epoch=b.sky.scene.epoch;refresh=b.sky.scene.refresh;}
 static NativeRetainedScene capture(byte[] background,NativeSourceSceneBinding.Source road,NativeSourceSceneBinding.Source wall,NativeSourceSceneBinding.Source proof){return capture(background,road,wall,proof,null);}
 static NativeRetainedScene capture(byte[] background,NativeSourceSceneBinding.Source road,NativeSourceSceneBinding.Source wall,NativeSourceSceneBinding.Source proof,NativeWorkProfile profile){
  if(background==null)return null;long start=NativeWorkProfile.start(profile);NativeBackgroundScene b=new NativeBackgroundScene(background);NativeWorkProfile.end(profile,NativeWorkProfile.CAPTURE_BG_PARSE,start);return retainValidated(b,road,wall,proof,profile);
 }
 /** Reuse a fully validated, immutable background; history/proof still validates normally. */
 static NativeRetainedScene capturePrepared(NativeSourceBackgroundBinding.Bound bound,NativeSourceSceneBinding.Source road,NativeSourceSceneBinding.Source wall,NativeSourceSceneBinding.Source proof,NativeWorkProfile profile){
  if(bound==null)return null;long start=NativeWorkProfile.start(profile);NativeBackgroundScene b=bound.background;NativeWorkProfile.end(profile,NativeWorkProfile.CAPTURE_BG_PARSE,start);return retainValidated(b,road,wall,proof,profile);
 }
 private static NativeRetainedScene retainValidated(NativeBackgroundScene b,NativeSourceSceneBinding.Source road,NativeSourceSceneBinding.Source wall,NativeSourceSceneBinding.Source proof,NativeWorkProfile profile){
  if(road==null||wall==null||proof==null)throw new IllegalArgumentException("Retained providers required");long start;NativeSceneSnapshot scene=b.sky.scene;int count=scene.geometryCount();NativeRoadHistory[] roads=new NativeRoadHistory[count];NativeWallHistory[] walls=new NativeWallHistory[count];byte[][] proofs=new byte[count][];
  for(int i=0;i<count;i++){NativeScenePacket p=scene.geometry(i);start=NativeWorkProfile.start(profile);byte[] r=road.packet(scene.epoch,p.serial,p.beginRefresh,p.endRefresh),w=wall.packet(scene.epoch,p.serial,p.beginRefresh,p.endRefresh),o=proof.packet(scene.epoch,p.serial,p.beginRefresh,p.endRefresh);NativeWorkProfile.end(profile,NativeWorkProfile.CAPTURE_HISTORY_COPY,start);if(r==null||w==null||o==null)return null;start=NativeWorkProfile.start(profile);roads[i]=new NativeRoadHistory(r);walls[i]=new NativeWallHistory(w);proofs[i]=o;NativeWorkProfile.end(profile,NativeWorkProfile.CAPTURE_HISTORY_PARSE,start);}
  start=NativeWorkProfile.start(profile);NativeRoadRetention r=new NativeRoadRetention(scene,roads,proofs);NativeWorkProfile.end(profile,NativeWorkProfile.CAPTURE_ROAD_RETAIN,start);start=NativeWorkProfile.start(profile);NativeWallRetention w=new NativeWallRetention(scene,walls,proofs);NativeWorkProfile.end(profile,NativeWorkProfile.CAPTURE_WALL_RETAIN,start);return new NativeRetainedScene(b,r,w,profile);
 }
}

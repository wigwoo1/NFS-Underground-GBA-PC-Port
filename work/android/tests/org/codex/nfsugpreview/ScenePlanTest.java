package org.codex.nfsugpreview;
import java.nio.file.*;
public class ScenePlanTest {public static void main(String[] args)throws Exception{
 int accepted=0,rejected=0,commands=0,triangles=0;
 try(DirectoryStream<Path> files=Files.newDirectoryStream(Paths.get(args[0]),"*.nsp")){for(Path file:files){if(file.getFileName().toString().startsWith("bad-"))continue;
 NativeScenePacket packet=new NativeScenePacket(1,Files.readAllBytes(file));NativeWorldScene world=new NativeWorldScene(packet);
 boolean supported=true;for(int i=0;i<world.surfaceCount();i++){NativeWorldScene.Surface s=world.surface(i);supported&=(s.lit?((s.mode==3||s.mode==8)&&s.corners==4):(s.mode==0||s.mode==1||s.mode==2||s.mode==4||s.mode==5||s.mode==6||s.mode==7));}
 try{NativeSceneDrawPlan plan=new NativeSceneDrawPlan(packet);if(!supported)throw new AssertionError("Unsupported accepted");
 if(plan.count()!=world.commandCount())throw new AssertionError();for(int i=0;i<plan.count();i++){NativeSceneDrawPlan.Draw d=plan.draw(i);NativeWorldScene.Command c=world.command(i);if(d.index!=c.index||d.model!=c.model||d.mesh().remaining()!=d.vertices*5||d.image().remaining()!=d.width*d.height*4)throw new AssertionError();commands++;triangles+=d.vertices/3;}accepted++;
 }catch(IllegalArgumentException e){if(supported)throw e;rejected++;}
 }}if(accepted==0||rejected==0)throw new AssertionError();System.out.println("PASS_SCENE_PLAN accepted="+accepted+" unsupported="+rejected+" ordered_commands="+commands+" triangles="+triangles);
 }}
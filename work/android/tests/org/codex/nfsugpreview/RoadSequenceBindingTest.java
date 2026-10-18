package org.codex.nfsugpreview;
import java.nio.file.*;import java.util.*;
public class RoadSequenceBindingTest{
 public static void main(String[] args)throws Exception{Path dir=Paths.get(args[0]);NativeRoadBindings.Candidate[] candidates=RoadBindingsTest.candidates(dir,0);int accepted=0,rejected=0,roads=0;try(DirectoryStream<Path> files=Files.newDirectoryStream(dir,"race-background-*.nrb")){for(Path file:files){NativeSceneSnapshot scene=new NativeBackgroundScene(Files.readAllBytes(file)).sky.scene;try{NativeRoadBindings binding=new NativeRoadBindings(scene,candidates);accepted++;roads+=binding.count();}catch(IllegalArgumentException e){rejected++;System.out.println("REJECT "+file.getFileName()+" "+e.getMessage());}}}if(accepted==0)throw new AssertionError("No positive scene bindings");System.out.println("SEQUENCE_BINDING_AUDIT accepted="+accepted+" rejected="+rejected+" roads="+roads);}
}

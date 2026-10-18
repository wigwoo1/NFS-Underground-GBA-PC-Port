package org.codex.nfsugpreview;
public class EmptyRoadProofTest{
 public static void main(String[] args){long[] identity={1,0x030000c0,0x08000000,8,0};int[] proof={6,1,0,4,1,0,0,0,2,15,0,158,0,0,0,0};NativeRoadBindings.verifiedEmpty(2,10,11885,11890,0,identity,proof);int rejected=0;for(int field:new int[]{0,1,2,3,4,5,6,7,8,9,10,11}){int[] bad=proof.clone();bad[field]=field==3?33:field>=8?241:proof[field]^1;try{NativeRoadBindings.verifiedEmpty(2,10,11885,11890,0,identity,bad);throw new AssertionError("Accepted bad proof "+field);}catch(IllegalArgumentException expected){rejected++;}}System.out.println("PASS_EMPTY_ROAD_PROOF malformed="+rejected);}
}

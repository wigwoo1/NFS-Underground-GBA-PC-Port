from analyze_long_interval_partition_candidate import union_ns
assert union_ns([(0,10),(3,7),(8,15)],0,20)==15
assert union_ns([(-5,5),(15,25)],0,20)==10
assert union_ns([(0,10),(10,20)],0,20)==20
assert union_ns([(30,40)],0,20)==0
assert union_ns([],0,20)==0
stages=[(10,30),(40,50)];gc=[(20,45),(25,35)]
stage=union_ns(stages,0,60);collection=union_ns(gc,0,60);combined=union_ns(stages+gc,0,60)
assert (stage,collection,combined)==(30,25,40)
assert (collection-(combined-stage),combined-stage,60-combined)==(15,10,20)
print('PASS_CLIPPED_NESTED_GC_STAGE_PARTITION')

from pathlib import Path
p=Path('work/camera/analyze_producer_gaps.py');s=p.read_text();needle='assert gaps\nout=';assert needle in s;s=s.replace(needle,"""assert gaps
cpu_path=Path(str(p)+'-producer-cpu.csv')
if cpu_path.exists():
 cpu_rows=list(csv.DictReader(cpu_path.open()))
 for gap in gaps:
  lo,hi=gap['begin_ns'],gap['end_ns']
  for kind in ('original_tick','submission'):
   overlapping=[r for r in cpu_rows if r['kind']==kind and int(r['begin_ns'])<hi and int(r['end_ns'])>lo]
   assert all(int(r['valid'])==1 and int(r['cpu_end_ns'])>=int(r['cpu_begin_ns']) for r in overlapping)
   gap[kind+'_full_overlapping_cpu_ms']=sum(int(r['cpu_end_ns'])-int(r['cpu_begin_ns']) for r in overlapping)/1e6
   gap[kind+'_full_overlapping_wall_ms']=sum(int(r['end_ns'])-int(r['begin_ns']) for r in overlapping)/1e6
out=""",1);p.write_text(s)

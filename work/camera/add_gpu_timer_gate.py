from pathlib import Path
p=Path('work/camera/audit_threaded_racing_motion.py');s=p.read_text();needle="rate=16777216/(280896*60)";assert needle in s;s=s.replace(needle,"if os.environ.get('NF_TEST_GPU_TIMESTAMPS')=='1':\n assert stats['gpu_timer_started']==stats['gpu_timer_resolved']==stats['rendered'] and stats['gpu_timer_started']>0 and stats['gpu_timer_pending']==0\n"+needle,1);p.write_text(s)

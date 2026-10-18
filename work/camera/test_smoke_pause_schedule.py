from owned_smoke_pause_schedule import SmokePauseSchedule
s=SmokePauseSchedule((1,10,20))
assert not s.paused(.9)
assert s.paused(1.5) and s.paused(1.6) and not s.paused(1.8)
assert not s.paused(9)
assert s.paused(12) and s.paused(12.1) and not s.paused(12.3)
assert s.paused(30) and s.paused(30.1) and not s.paused(30.3) and not s.paused(40)
assert s.index==3
empty=SmokePauseSchedule(())
assert not empty.paused(100)
print('PASS: late observations trigger all three pauses exactly once, full observed duration, empty schedule neutral')

"""Original first-pass deferral and low-eight-bit second-pass mask ownership."""
def sampled_wall_emitted(flags,edge,count):
 if not 0<=edge<count<=32:raise ValueError('Invalid deferred wall source ring')
 if not flags&2:return True
 # Original ARM shift by remaining vertices; region action retains mask&255.
 bit=0 if count-edge>=32 else 1<<(count-edge)
 if not bit&255:return False
 raise ValueError('Unverified sampled graph deferred placement')

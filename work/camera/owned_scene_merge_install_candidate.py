import owned_closed_scene_memory as memory
from owned_closed_scene_merge_candidate import ClosedSceneMemory as Base
stats={'constructions':0,'ranges':0,'owned_bytes':0}
class SelectedMemory(Base):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs)
  stats['constructions']+=1;stats['ranges']+=len(self._ranges);stats['owned_bytes']+=self.owned_byte_count
memory.ClosedSceneMemory=SelectedMemory

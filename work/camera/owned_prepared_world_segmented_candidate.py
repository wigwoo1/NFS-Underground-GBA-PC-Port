"""Isolated complete-world sampling with private prefix and retained source tail."""
from owned_prepared_world_release_candidate import PreparedWorldMotion as Base
from owned_sampled_world_segmented_candidate import assemble_world
class PreparedWorldMotion(Base):
 def sample(self,alpha):
  if self.history is None:raise ValueError('Prepared world interval closed')
  return assemble_world(self.pair,self.roads,self.endpoint_roads,alpha,self.rom)

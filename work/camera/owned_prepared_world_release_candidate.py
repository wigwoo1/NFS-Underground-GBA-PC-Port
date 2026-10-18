"""Isolated release of closed prepared-world graphs; numeric diagnostics retained."""
from owned_prepared_world_motion import PreparedWorldMotion as Base
class PreparedWorldMotion(Base):
 def close(self):
  super().close()
  self.pair=None
  self.roads=None
  self.endpoint_roads=()
  self.rom=None

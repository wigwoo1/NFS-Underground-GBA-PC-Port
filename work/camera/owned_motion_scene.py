"""Immutable complete scene ownership for motion visibility sampling."""
from dataclasses import dataclass
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_model_builder_inputs import OwnedModelBuilders
from owned_model_sources import OwnedModelSources
from owned_sky_boundary import SceneSky
from owned_closed_viewport import ClosedViewport
@dataclass(frozen=True)
class MotionScene:
 graph:ClosedGraph
 supplements:ClosedSupplements
 builders:OwnedModelBuilders|None=None
 sources:OwnedModelSources|None=None
 sky:SceneSky|None=None
 viewport:ClosedViewport|None=None
 def match(self,frame):
  self.graph.match_frame(frame)
  if self.viewport is not None:self.viewport.validate_for(self.graph)
  if (self.graph.epoch,self.graph.refresh,self.graph.graph.refresh)!=(self.supplements.epoch,self.supplements.refresh,self.supplements.source_refresh):raise ValueError('Unpaired motion scene ownership')
  if self.builders is not None and any(value.refresh>self.graph.refresh for values in self.builders.records.values() for value in values):raise ValueError('Future builder in motion scene')
  if self.sources is not None and (self.sources.epoch,self.sources.refresh,self.sources.source_refresh)!=(self.graph.epoch,self.graph.refresh,self.graph.graph.refresh):raise ValueError('Unpaired model source scene')
  if self.sky is not None:self.sky.match_graph(self.graph)
  return self
 @property
 def identity(self):return self.graph.epoch,self.graph.refresh


"""Construct unchanged frozen road record type with one private field dictionary."""
from owned_complete_road_candidates import RoadCandidate
from owned_road_material_decode_reuse_candidate import source,ns

def record(descriptor,secondary,material_index,descriptor_bytes,vertices,offsets,face_address,face,material,animation,texture,missing):
 result=object.__new__(RoadCandidate)
 result.__dict__.update(descriptor=descriptor,secondary=secondary,material_index=material_index,descriptor_bytes=descriptor_bytes,vertices=vertices,offsets=offsets,face_address=face_address,face=face,material=material,animation=animation,texture=texture,missing=missing)
 return result
namespace=dict(ns,RoadCandidate=record);exec(compile(source,'road-record-construction-candidate','exec'),namespace)
road_candidates=namespace['road_candidates']

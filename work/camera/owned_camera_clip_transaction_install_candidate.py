"""Default-off current sampled-road transaction selection."""
import owned_sampled_road_sequence as sequence
from owned_camera_clip_transaction import clipped_camera_road as transaction
stats=dict(calls=0)
original=sequence.clipped_camera_road
installed=False
def selected(*args,**kwargs):
 stats['calls']+=1
 return transaction(*args,**kwargs)
def install():
 global installed
 if installed:return
 sequence.clipped_camera_road=selected;installed=True
def uninstall():
 global installed
 if not installed:return
 if sequence.clipped_camera_road is not selected:raise RuntimeError('Road transaction installer ownership changed')
 sequence.clipped_camera_road=original;installed=False

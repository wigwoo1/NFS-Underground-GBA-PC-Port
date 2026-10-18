import owned_source_process_sidecar_candidate as base
from owned_extent_validated_sidecar_encode_candidate import encode
base.encode.__globals__['decode']=encode.__globals__['decode']

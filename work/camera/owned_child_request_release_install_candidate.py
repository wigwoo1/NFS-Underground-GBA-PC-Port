"""Release completed request locals after synchronous result/trace publication."""
import owned_endpoint_reference_process_service_candidate as base
source=base.source
needle="   except BaseException as error:\n    if prepared is not None:prepared.close()"
assert source.count(needle)==1
# The finally executes after successful synchronous trace send or error response.
marker="    connection.send(('error',repr(error),0))\n finally:\n"
assert source.count(marker)==1
release="    connection.send(('error',repr(error),0))\n   finally:\n    a=sa=b=sb=encoded=samples=sidecar=None\n    construct_trace=sample_trace=encode_trace=None\n finally:\n"
source=source.replace(marker,release)
namespace=dict(base.reference_child.__globals__)
exec(compile(source,'child-completed-request-release','exec'),namespace)
base.reference_child=namespace['reference_child']

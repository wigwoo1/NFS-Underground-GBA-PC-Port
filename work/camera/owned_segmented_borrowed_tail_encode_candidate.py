"""Borrow immutable byte owners only for synchronous shared mapping writes."""
import inspect,textwrap
import owned_segmented_process_encode_candidate as base
source=textwrap.dedent(inspect.getsource(base.encode_samples))
source=source.replace(" if borrow_tails:raise ValueError('Segmented transport requires owned immutable tail bytes')", " if not borrow_tails:raise ValueError('Borrowed encoder requires shared output')")
source=source.replace('tails.append(bytes(tail))','tails.append(tail)')
namespace=dict(base.encode_samples.__globals__)
exec(compile(source,'segmented-borrowed-tail-encode','exec'),namespace)
encode_samples=namespace['encode_samples']

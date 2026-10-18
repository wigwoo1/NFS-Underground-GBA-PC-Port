"""Diagnostic finer copy/upload and immutable HUD owner boundaries."""
import inspect,textwrap,time
from owned_thread_cycles import read as thread_cycles
import owned_hud_shared_library_binding_candidate as binding
from pathlib import Path
# Extend the isolated renderer installer before compiling its copied methods.
source=Path(__file__).with_name('owned_prepare_cpu_trace_install_candidate.py').read_text()
marker=" source=textwrap.dedent(ast.get_source_segment(source,method))"
assert source.count(marker)==1
addition="""
 source=source.replace('ts=(C.c_uint*2)();', "stage('vertices_copy_convert');ts=(C.c_uint*2)();")
 source=source.replace('assert d.nf_d3d_material_packet_cached(tb,nb,tr,nt,nt*16)==0', "stage('texture_packet_copy');assert d.nf_d3d_material_packet_cached(tb,nb,tr,nt,nt*16)==0")
 source=source.replace("stage('material_copy_upload')", "stage('material_cached_upload')")
"""
source=source.replace(marker,marker+addition)
# Snapshot diagnostics are copied into the immutable bounded long-event ledger.
source=source.replace('snapshot_thread_cycles=snapshot_cycle_end-snapshot_cycle_begin,',"snapshot_constructor_stages=snapshot.constructor_stages if snapshot_new else [],snapshot_thread_cycles=snapshot_cycle_end-snapshot_cycle_begin,")
ns=dict(__file__=str(Path(__file__).with_name('owned_prepare_cpu_trace_install_candidate.py')))
exec(compile(source,'prepare-split-install','exec'),ns)
method=binding.HudFrameSnapshot.__init__;source=textwrap.dedent(inspect.getsource(method))
source=source.replace('if type(base) is not bytes',"ticks=[time.perf_counter_ns()];cycles=[thread_cycles()];self.constructor_stages=[]\n def mark(name):\n  now=time.perf_counter_ns();cy=thread_cycles();self.constructor_stages.append(dict(stage=name,elapsed_ns=now-ticks[-1],thread_cycles=cy-cycles[-1]));ticks.append(now);cycles.append(cy)\n if type(base) is not bytes")
source=source.replace('self._base=base;',"mark('validate_envelope');self._base=base;")
source=source.replace('retained=C.c_char_p(base);',"mark('bind_library');retained=C.c_char_p(base);")
source=source.replace('self.token=d.nf_hud_owner_create',"mark('immutable_pointer');self.token=d.nf_hud_owner_create")
source=source.replace('if not self.token:',"mark('native_owner_create');\n if not self.token:")
ns=dict(method.__globals__);ns.update(time=time,thread_cycles=thread_cycles)
exec(compile(source,'hud-constructor-split','exec'),ns);binding.HudFrameSnapshot.__init__=ns['__init__']

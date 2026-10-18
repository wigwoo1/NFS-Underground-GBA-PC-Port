"""Instrument the qualified inner prepare, preserving outer HUD wrappers."""
import dis
import sys
from session_post_consumer_transform import transform

def signature(method):
    return [(item.opname,item.argval) for item in dis.get_instructions(method)]

def install():
    import owned_hud_borrowed_rows_install_candidate as borrowed
    import owned_source_packet_phase_profile_install_candidate as packet
    if getattr(borrowed,'session_post_consumer_installed',False):return
    original=borrowed.original_prepare
    if original.__code__.co_filename=='hud-session-native-boundaries':
        source=packet.source
    elif original.__code__.co_filename=='native-input-draw-boundaries':
        selected=sys.modules.get('owned_native_draw_boundaries_install_candidate')
        if selected is None:raise RuntimeError('Native draw boundary module not selected')
        source=selected.source
    else:
        raise RuntimeError('Unexpected inner session installation chain: '+original.__code__.co_filename)
    namespace=dict(original.__globals__)
    exec(compile(source,'session-source-qualification','exec'),namespace)
    if signature(namespace['prepare'])!=signature(original):
        raise RuntimeError('Authoritative generated session source mismatch')
    exec(compile(transform(source),'session-post-consumer-boundaries','exec'),namespace)
    borrowed.original_prepare=namespace['prepare']
    borrowed.session_post_consumer_installed=True

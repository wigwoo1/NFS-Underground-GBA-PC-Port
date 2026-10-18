"""Conservative provenance gate derived from current HUD composition shader."""
def hud_background_passthrough(control,object_alpha,text_alpha,owned_text_enabled,blend,brightness):
    # Native background must survive windows; no foreground OBJ or text replacement.
    if not control & 4 or (control & 16 and object_alpha > 127) or (owned_text_enabled and text_alpha > 127):
        return False
    mode=(blend>>6)&3 if control & 32 else 0
    # With no OBJ, alpha may still blend BG with backdrop.
    if mode==1 and blend & 4 and blend & 8192:
        return False
    if mode in (2,3) and blend & 4 and min(brightness & 31,16):
        return False
    return True

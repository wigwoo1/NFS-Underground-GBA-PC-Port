"""Keep display diagnostics while selecting the isolated HUD lease session."""
import owned_segmented_display_placement_install_candidate as display
import owned_native_source_segmented_release_worker_candidate as worker
import owned_native_source_hud_build_split_session_candidate as hud
hud.OwnedD3DConsumer=display.OwnedD3DConsumer
assert worker.NativeFrameIdentityError is hud.NativeFrameIdentityError
class HudDisplaySession(hud.NativeSourceSession,display.DisplaySession):
 present=display.DisplaySession.present
worker.NativeSourceSession=HudDisplaySession

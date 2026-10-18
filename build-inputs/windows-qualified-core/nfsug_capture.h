#ifndef NFA_CAPTURE_H
#define NFA_CAPTURE_H
#include "nfsug_android_core.h"
/* Same owner thread as the core. Closed geometry packets copied synchronously.
   Diagnostic capture only: sky/HUD/index metadata integration is not implied.
   stats: enabled,epoch,closed,published,rejected,failed,latest_bytes,serial.
   Copy with NULL queries size. Discard old epoch data on load/mode changes. */
NFA_API int nfa_core_capture_enable(NFAAndroidCore*,int);
NFA_API int nfa_core_capture_stats(NFAAndroidCore*,uint64_t out[8]);
NFA_API size_t nfa_core_capture_copy(NFAAndroidCore*,void*,size_t);
/* Optional historical auxiliary rows: all VRAM/palette/OAM plus scanline registers.
   Owner-thread calls only; caller owns copied bytes. No geometry pairing implied. */
NFA_API int nfa_core_capture_layers(NFAAndroidCore*,int);
NFA_API int nfa_core_capture_layer_info(NFAAndroidCore*,uint64_t out[5]);
NFA_API size_t nfa_core_capture_layer_row(NFAAndroidCore*,uint64_t,unsigned,unsigned,void*,size_t);
/* Whole displayed refresh only; rejects split/mutating pages and stale epochs.
   out: epoch,serial,end,page,generation,audit_version,refresh,context_kind. */
NFA_API int nfa_core_capture_pair(NFAAndroidCore*,unsigned,uint64_t out[8]);
/* Exact retained owner lookup. Caller copies; old epoch/serial rejects. */
NFA_API size_t nfa_core_capture_owned_packet(NFAAndroidCore*,uint64_t,unsigned,void*,size_t);
/* One old-to-new page switch only; out: epoch,old/new serial,old/new end,
   old/new page,old/new generation,audit version,refresh,first newer row. */
NFA_API int nfa_core_capture_split(NFAAndroidCore*,unsigned,uint64_t out[12]);
/* Same eight metadata words as capture_pair; exactly one of both retained
   owners must match the entire scanout. Ambiguity rejects atomically. */
NFA_API int nfa_core_capture_display_owner(NFAAndroidCore*,unsigned,uint64_t out[8]);
/* Diagnostic uint64_t[664]: header epoch/refresh/mode/frontend/kind/audit/
   row_count/schema; two owners of epoch/serial/begin/end/page/generation/audit/
   present; then 160 rows of display_control/page0gen/page1gen/audit.
   Historical rows plus packet completion provenance, not a rendering approval.
   NULL queries size; wrong epoch/refresh/short capacity rejects atomically. */
NFA_API size_t nfa_core_capture_provenance(NFAAndroidCore*,uint64_t,unsigned,void*,size_t);
/* NAB1 owned combined snapshot, 16 uint64 header words: magic/version/total/
   epoch/refresh/kind/cut/count, then four offset/size pairs for old-or-whole
   geometry, new geometry (empty for whole), compact NLP1 layers, provenance.
   Initial/unowned/stale data rejects; caller owns all copied bytes. */
NFA_API size_t nfa_core_capture_bundle(NFAAndroidCore*,uint64_t,unsigned,void*,size_t);
/* Opt-in source-regenerated scene endpoints. Requires capture first. Enabling
   copies immutable loaded ROM assets; no file path or test environment flags.
   Exact epoch/serial/begin/end ownership, NULL size query, caller-owned copy.
   Stale/short/disabled requests reject without writing output. Not a complete
   displayed sky/background/HUD snapshot or interpolated presentation frame. */
NFA_API int nfa_core_capture_source_world_enable(NFAAndroidCore*,int);
NFA_API size_t nfa_core_capture_source_world(NFAAndroidCore*,uint64_t,unsigned,unsigned,unsigned,void*,size_t);
/* Original wall-source component, opt-in owner thread. Initializes source replay
   without paths/test flags. NWH1 copies for the last two exact completed owners.
   Does not include sky/background/road ownership or authorize live composition. */
NFA_API int nfa_core_capture_wall_history_enable(NFAAndroidCore*,int);
NFA_API size_t nfa_core_capture_wall_history(NFAAndroidCore*,uint64_t,unsigned,unsigned,unsigned,void*,size_t);
NFA_API int nfa_core_capture_wall_history_stats(NFAAndroidCore*,uint64_t[8]);
/* NRP1 source-write kind/refresh proof, frozen with the same wall owner. */
NFA_API size_t nfa_core_capture_write_ownership(NFAAndroidCore*,uint64_t,unsigned,unsigned,unsigned,void*,size_t);
/* NRH1 compact source runs/assets frozen with wall/proof ownership. */
NFA_API size_t nfa_core_capture_road_history(NFAAndroidCore*,uint64_t,unsigned,unsigned,unsigned,void*,size_t);
/* Original sky and initial source background, not a full live renderer frame. */
NFA_API int nfa_core_capture_sky_enable(NFAAndroidCore*,int);
NFA_API size_t nfa_core_capture_sky(NFAAndroidCore*,uint64_t,unsigned,void*,size_t);
NFA_API size_t nfa_core_capture_sky_scene(NFAAndroidCore*,uint64_t,unsigned,void*,size_t);
NFA_API size_t nfa_core_capture_background_scene(NFAAndroidCore*,uint64_t,unsigned,void*,size_t);
#endif

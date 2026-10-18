#ifndef NFA_OWNED_TEXT_H
#define NFA_OWNED_TEXT_H
#include "nfsug_capture.h"
/* Opt-in original glyph-asset observer, same owner thread. Re-enable after epoch changes.
   Does not relax original frontend/racing diagnostic guards or modify game memory. */
NFA_API int nfa_core_capture_text_enable(NFAAndroidCore*,int);
/* NFT1 eight uint64 header words:magic/version/total/epoch/refresh/240/160/schema1,
   then38400 source indices and38400 coverage bytes. Requires an owned NAB1 refresh.
   No output change on failure; NULL queries only validated complete data. */
NFA_API size_t nfa_core_capture_text(NFAAndroidCore*,uint64_t,unsigned,void*,size_t);
/* NMT1 ten uint64 words:magic/version/total/epoch/refresh/240/160/mode/frontend/kind2,
   then38400 indices and38400 coverage. Complete historical verified 2D context only;
   no geometry owner implied. Same opt-in/lifetime and atomic failure rules as NFT1. */
NFA_API size_t nfa_core_capture_menu_text(NFAAndroidCore*,uint64_t,unsigned,void*,size_t);
/* NMB1 atomic text/palette pair: eight uint64 magic/version/total/epoch/refresh/
   textbytes/palettebytes/reserved0, then complete NMT1 and NMP1 payloads.
   Owner-thread only; every section validated before any caller output changes. */
NFA_API size_t nfa_core_capture_menu_text_bundle(NFAAndroidCore*,uint64_t,unsigned,void*,size_t);
/* Optional existing source-copy collector. Sky is keyed to completed scene serial,
   NOT display refresh; NFSK15192bytepayload retains original epoch/copyrefresh.
   Historical palettes/background ownership must be joined separately. */
NFA_API int nfa_core_capture_sky_enable(NFAAndroidCore*,int);
NFA_API size_t nfa_core_capture_sky(NFAAndroidCore*,uint64_t,unsigned,void*,size_t);
/* NSB1: sixteen uint64 header words magic/version/total/epoch/refresh/kind/cut/count,
   four offset/size pairs: NAB1,sky0+asset0,sky1+asset1,empty. Each sky+asset is30568bytes.
   Includes displayed historical palettes in embedded NAB1; no initial fill coverage implied. */
NFA_API size_t nfa_core_capture_sky_scene(NFAAndroidCore*,uint64_t,unsigned,void*,size_t);
#endif





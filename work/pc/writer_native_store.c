#include "writer_shared_store.c"
#include "writer_native_scene.h"
int nf_pc_writer_store_set_maximum(NFRecipeStore*s,size_t maximum){if(!owner(s)||maximum>LIMIT||(uint64_t)used(s->ledger)>maximum)return 0;s->ledger->maximum=maximum;return 1;}

#include <stddef.h>
#include <math.h>
__declspec(dllexport) int nf_owned_finite_doubles(const double *v,size_t n){if(!v && n)return 0;for(size_t i=0;i<n;i++)if(!isfinite(v[i]))return 0;return 1;}

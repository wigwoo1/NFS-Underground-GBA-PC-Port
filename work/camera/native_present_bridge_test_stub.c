static int status,calls;
__declspec(dllexport) void test_set(int value){status=value;calls=0;}
__declspec(dllexport) int test_present(void){calls++;return status;}
__declspec(dllexport) int test_calls(void){return calls;}

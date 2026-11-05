// The three status descriptions share TextBox with unrelated game UI.
// Select their dictionaries only while the original status call is drawing.
thread_local const char* statusTextContext=nullptr;

const char* statusTextContextAt(uintptr_t caller){
 switch(caller){
  case 0x100130f5cULL:return "status-nutrition";
  case 0x100130fc7ULL:return "status-warmth";
  case 0x10013100eULL:return "status-vigour";
  default:return nullptr;
 }
}

void statusTextBox(int x,int y,int width,char* source,int color){
 auto fn=original<void(*)(int,int,int,char*,int)>("status_text_box");
 const uintptr_t caller=(uintptr_t)__builtin_return_address(0)-_dyld_get_image_vmaddr_slide(0);
 const char* previous=statusTextContext;
 statusTextContext=statusTextContextAt(caller);
 fn(x,y,width,source,color);
 statusTextContext=previous;
}

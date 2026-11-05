thread_local bool drawingProfileName=false;

void heldItemBar(int x,int y,int width,char* text,int style){
 auto draw=original<void(*)(int,int,int,char*,int)>("held_item_bar");
 // Nayta_Wieldatut uses this call only for occupied slots.
 const uintptr_t caller=(uintptr_t)__builtin_return_address(0);
 const uintptr_t callSite=caller-_dyld_get_image_vmaddr_slide(0);
 if(callSite==0x1001168bcULL){
  const bool previous=drawingProfileName;
  drawingProfileName=true;
  draw(x,y,width,text,style);
  drawingProfileName=previous;
  return;
 }
 // draw_profile sends the formatted height and weight to these two bars.
 if(callSite==0x100116c93ULL||callSite==0x100116cfcULL){
  const bool previous=drawingProfileUnit;
  drawingProfileUnit=true;
  draw(x,y,width,text,style);
  drawingProfileUnit=previous;
  return;
 }
 if(callSite!=0x10013082eULL){draw(x,y,width,text,style);return;}
 const bool previous=drawingItems;
 drawingItems=true;
 draw(x,y,width,text,style);
 drawingItems=previous;
}

// Piirra_Nappain renders the hotkey and every other button letter separately.
// Keep its background, hotkey, cursor advances, and hitboxes on the native path.
struct ArmorButtonFrame {
 NSString* label;
 int x, y, width;
 bool painted=false;
};
thread_local ArmorButtonFrame* activeArmorButton=nullptr;

#include "craft_prompt.inc"

void armorButton(int x,int y,char* source){@autoreleasepool{
 auto fn=original<void(*)(int,int,char*)>("armor_button");
 if(depth||!source){fn(x,y,source);return;}
 if(drawCraftProceedButton(fn,(uintptr_t)__builtin_return_address(0)-_dyld_get_image_vmaddr_slide(0),x,y,source))return;
 // The native button starts 8 px in and advances 8 px for every glyph,
 // including spaces. The markup brackets do not advance the cursor.
 // Armor entries have one marked hotkey followed by the remaining letters.
 const char* hotkey=strchr(source,'<');
 const char* dot=strchr(source,'.');
 if(!hotkey||(dot&&dot<hotkey+3)||strlen(hotkey)<4||hotkey[2]!='>'){
  fn(x,y,source);return;
 }
 const char* end=dot?dot:source+strlen(source);
 NSString* english=[[NSString alloc] initWithBytes:hotkey+3 length:end-(hotkey+3) encoding:NSASCIIStringEncoding];
 if(!english){fn(x,y,source);return;}
 NSString* key=[NSString stringWithFormat:@"armor-button\t%c%@",hotkey[1],normalize(english)];
 refreshConfig();
 NSString* label=state().enabled?state().dictionary[key]:nil;
 if(!label){fn(x,y,source);return;}
 const int labelCells=(int)(end-(hotkey+3));
 const int leadingCells=(int)(hotkey-source);
 if(labelCells<2){fn(x,y,source);return;}
 ArmorButtonFrame frame{label,x+8*(2+leadingCells),y+5,labelCells*8};
 auto* previous=activeArmorButton;
 activeArmorButton=&frame;
 fn(x,y,source);
 activeArmorButton=previous;
}}

bool prepareArmorButton(int x,int y,const char* source,unsigned color){
 auto* frame=activeArmorButton;
 if(!frame||y!=frame->y||x<frame->x||x>=frame->x+frame->width||!source[0]||source[1])return false;
 if(x==frame->x)frame->painted=drawSurface(x,y,frame->label,color,frame->width);
 return frame->painted;
}

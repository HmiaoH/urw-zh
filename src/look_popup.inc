// The native creature modal uploads screen to tex, renders the map, then
// copies the window rectangle back over it. Use an explicit destination
// rectangle so SDL keeps its normal viewport and logical-size transform.
extern "C" int SDL_RenderSetClipRect(SDL_Renderer*,const SDL_Rect*);
extern "C" int SDL_GetTextureBlendMode(SDL_Texture*,int*);

bool copyLookPopup(SDL_Rect source){
 auto& s=state();
 auto* renderer=s.ren?*s.ren:nullptr;
 auto* texture=s.screenTexture?*s.screenTexture:nullptr;
 auto* screen=s.screen?*s.screen:nullptr;
 if(!renderer||!texture||!screen||!s.convert||SDL_GetRenderTarget(renderer))return false;
 if(source.w!=300||source.h<=0||source.h>screen->h)return false;

 // Clip in native screen coordinates before converting the destination.
 int right=std::min(source.x+source.w,screen->w);
 int bottom=std::min(source.y+source.h,screen->h);
 source.x=std::max(source.x,0);
 source.y=std::max(source.y,0);
 source.w=right-source.x;
 source.h=bottom-source.y;
 if(source.w<=0||source.h<=0)return false;
 SDL_Rect destination=source;
 s.convert(&destination);

 int blendMode;
 if(SDL_GetTextureBlendMode(texture,&blendMode)!=0)return false;
 if(blendMode&&SDL_SetTextureBlendMode(texture,0)!=0)return false;
 const bool clipped=SDL_RenderIsClipEnabled(renderer);
 SDL_Rect previousClip{};
 if(clipped)SDL_RenderGetClipRect(renderer,&previousClip);
 bool ready=!clipped||SDL_RenderSetClipRect(renderer,nullptr)==0;
 bool copied=ready&&SDL_RenderCopy(renderer,texture,&source,&destination)==0;
 if(clipped&&ready)SDL_RenderSetClipRect(renderer,&previousClip);
 if(blendMode)SDL_SetTextureBlendMode(texture,blendMode);
 return copied;
}

void flipScreenPortion(int x,int y,int width,int height,int present){
 auto fn=original<void(*)(int,int,int,int,int)>("flip_screen_portion");
 constexpr uintptr_t lookPopupReturn=0x1000cf902ULL;
 if(present||(uintptr_t)__builtin_return_address(0)!=lookPopupReturn+_dyld_get_image_vmaddr_slide(0)||
    !copyLookPopup({x,y,width,height})){
  fn(x,y,width,height,present);
 }
}

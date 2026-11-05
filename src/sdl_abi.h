#pragma once
// SDL 2 public C ABI subset. Opaque objects remain owned by the game.
#include <cstdint>
struct SDL_Renderer; struct SDL_Texture; struct SDL_PixelFormat;
struct SDL_Rect {int x,y,w,h;};
struct SDL_Color {uint8_t r,g,b,a;};
struct SDL_Surface {uint32_t flags;SDL_PixelFormat* format;int w,h,pitch;void* pixels;void* userdata;int locked;void* list_blitmap;SDL_Rect clip_rect;void* map;int refcount;};
extern "C" {
SDL_Surface* SDL_CreateRGBSurfaceFrom(void*,int,int,int,int,uint32_t,uint32_t,uint32_t,uint32_t);
void SDL_FreeSurface(SDL_Surface*);
int SDL_UpperBlit(SDL_Surface*,const SDL_Rect*,SDL_Surface*,SDL_Rect*);
int SDL_SetSurfaceBlendMode(SDL_Surface*,int);
uint32_t SDL_MapRGB(const SDL_PixelFormat*,uint8_t,uint8_t,uint8_t);
void SDL_GetRGB(uint32_t,const SDL_PixelFormat*,uint8_t*,uint8_t*,uint8_t*);
SDL_Texture* SDL_CreateTextureFromSurface(SDL_Renderer*,SDL_Surface*);
void SDL_DestroyTexture(SDL_Texture*);
int SDL_RenderCopy(SDL_Renderer*,SDL_Texture*,const SDL_Rect*,const SDL_Rect*);
SDL_Texture* SDL_GetRenderTarget(SDL_Renderer*);
int SDL_SetRenderTarget(SDL_Renderer*,SDL_Texture*);
int SDL_GetRendererOutputSize(SDL_Renderer*,int*,int*);
int SDL_QueryTexture(SDL_Texture*,uint32_t*,int*,int*,int*);
void SDL_RenderGetClipRect(SDL_Renderer*,SDL_Rect*);
int SDL_RenderIsClipEnabled(SDL_Renderer*);
int SDL_SetTextureBlendMode(SDL_Texture*,int);
const char* SDL_GetError();
}

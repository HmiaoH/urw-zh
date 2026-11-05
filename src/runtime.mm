#import <Foundation/Foundation.h>
#import <CoreText/CoreText.h>
#include <CommonCrypto/CommonDigest.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>
#include <mach-o/dyld.h>
#include <dlfcn.h>
#include <sys/mman.h>
#include <unistd.h>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <map>
#include <set>
#include <string>
#include <vector>
#include <chrono>
#include "sdl_abi.h"

namespace zh {
struct Hook {void* address;void* original;std::vector<uint8_t> bytes;};
struct State {
 std::map<std::string,Hook> hooks;
 NSDictionary* dictionary=nil; NSDictionary* config=nil; NSDictionary* segmented=nil;
 int *hyperX=nullptr,*hyperY=nullptr,*hyperLine=nullptr,*linkPos=nullptr,*npcX=nullptr,*npcY=nullptr,*playerX=nullptr,*playerY=nullptr;
 char *topics=nullptr,*linkList=nullptr;void(*spotEntry)(int,int,int,int,int)=nullptr;void(*line)(int,int,int,int)=nullptr;void(*flip)()=nullptr;
 NSArray* templates=nil; NSDictionary* itemRules=nil;
 std::set<std::string> seen;
 FILE* log=nullptr; FILE* missing=nullptr;
 SDL_Surface** screen=nullptr; SDL_Renderer** ren=nullptr; uint32_t* color=nullptr;int *x=nullptr,*y=nullptr;
 void (*convert)(SDL_Rect*)=nullptr;
 char* words=nullptr;
 char* noteText=nullptr;SDL_Rect* noteBox=nullptr;
 char* messageLogText=nullptr;char* messageLogFormat=nullptr;
 SDL_Rect* headingBox=nullptr;
 SDL_Texture** screenTexture=nullptr;
 int (*lineHeight)(float)=nullptr;void (*flipMap)()=nullptr;
 bool enabled=true; bool capture=true;
};
State& state(){static State* s=new State;return *s;}
thread_local int depth=0;
thread_local bool suppress=false;
void note(const char* msg){auto& s=state();if(s.log){fprintf(s.log,"%s\n",msg);fflush(s.log);}}
NSString* base(){Dl_info d{};dladdr((void*)&base,&d);return [[NSString stringWithUTF8String:d.dli_fname] stringByDeletingLastPathComponent];}
id json(NSString* path){NSData* b=[NSData dataWithContentsOfFile:path];return b?[NSJSONSerialization JSONObjectWithData:b options:0 error:nil]:nil;}
NSString* decode(const char* text){if(!text)return @"";NSString* s=[[NSString alloc] initWithUTF8String:text];return s?:[[NSString alloc] initWithBytes:text length:strlen(text) encoding:NSISOLatin1StringEncoding];}
NSString* normalize(NSString* s){
 if(!s)return @"";
 s=[[[s componentsSeparatedByCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]] filteredArrayUsingPredicate:[NSPredicate predicateWithFormat:@"length > 0"]] componentsJoinedByString:@" "];
 s=[s stringByReplacingOccurrencesOfString:@"\\s*(</?[A-Za-z]+>)\\s*" withString:@"$1" options:NSRegularExpressionSearch range:NSMakeRange(0,s.length)];
 return [s stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]];
}
// Game strings mix Latin-1 names with legacy resource bytes. Preserve byte identity
// in fallback decoding; resource compiler converts its CP437 source keys accordingly.
NSString* proseKey(NSString* s){return normalize([s stringByReplacingOccurrencesOfString:@"<br>" withString:@" "]);}
void loadCatalog();
void refreshConfig(){
 static auto next=std::chrono::steady_clock::time_point{};
 auto now=std::chrono::steady_clock::now();if(now<next)return;next=now+std::chrono::seconds(1);
 static NSDate* modified=nil;
 NSString* path=[base() stringByAppendingPathComponent:@"data/config.json"];
 NSDate* stamp=[[[NSFileManager defaultManager] attributesOfItemAtPath:path error:nil] fileModificationDate];
 if(!stamp||[stamp isEqual:modified])return;
 id config=json(path);if(![config isKindOfClass:[NSDictionary class]])return;
 modified=stamp;state().config=config;state().enabled=config[@"enabled"]?[config[@"enabled"] boolValue]:true;
 state().capture=config[@"capture"]?[config[@"capture"] boolValue]:true;loadCatalog();
}
NSString* matchTemplate(NSString* source,NSString* context){
 NSString* result=nil;
 for(NSDictionary* row in state().templates){
  if(![row[@"context"] isEqual:context])continue;
  NSRegularExpression* regex=row[@"regex"];NSTextCheckingResult* match=[regex firstMatchInString:source options:0 range:NSMakeRange(0,source.length)];
  if(!match)continue;
  // Ambiguous templates fail closed, preserving the original display.
  if(result)return nil;
  NSString* translation=row[@"translation"];NSArray* names=row[@"names"];
  NSRegularExpression* refs=[NSRegularExpression regularExpressionWithPattern:@"\\{([A-Za-z][A-Za-z0-9_]*)\\}" options:0 error:nil];
  NSMutableString* expanded=[NSMutableString new];NSUInteger cursor=0;
  for(NSTextCheckingResult* ref in [refs matchesInString:translation options:0 range:NSMakeRange(0,translation.length)]){
   [expanded appendString:[translation substringWithRange:NSMakeRange(cursor,ref.range.location-cursor)]];
   NSString* name=[translation substringWithRange:[ref rangeAtIndex:1]];NSUInteger index=[names indexOfObject:name];
   if(index==NSNotFound)return nil;
   [expanded appendString:[source substringWithRange:[match rangeAtIndex:index+1]]];cursor=NSMaxRange(ref.range);
  }
  [expanded appendString:[translation substringFromIndex:cursor]];result=expanded;
 }return result;
}
#include "items.inc"
#include "look_extra.inc"
#include "message_extra.inc"
#include "notification_rules.inc"
#include "craft_notification_extra.inc"
#include "dialogue_extra.inc"
#include "trade_rejection.inc"
#include "map_notification_extra.inc"
NSString* composeMemorial(NSString* source,const char* context);
NSString* translate(const char* text,const char* context,bool tradePayment=false){
 refreshConfig();
 auto& s=state();NSString* orig=decode(text);NSString* k=normalize(orig);if(!k.length)return nil;
 NSString* scoped=[NSString stringWithFormat:@"%s\t%@",context,k];
 NSString* result=s.dictionary[scoped]?:s.dictionary[k];
 if(!result&&!strcmp(context,"paragraph")){
  result=s.dictionary[[@"paragraph-prose\t" stringByAppendingString:proseKey(orig)]];
  if(result){
   // The game adds outer blank lines to clear the scenario picture. Keep that spacing.
   NSRange head=[orig rangeOfString:@"\\A(?:\\s*<br>)+\\s*" options:NSRegularExpressionSearch];
   NSRange tail=[orig rangeOfString:@"(?:\\s*<br>)+\\s*\\z" options:NSRegularExpressionSearch];
   if(head.location!=NSNotFound)result=[[orig substringWithRange:head] stringByAppendingString:result];
   if(tail.location!=NSNotFound)result=[result stringByAppendingString:[orig substringWithRange:tail]];
  }
 }
 if(!result&&!strcmp(context,"message"))result=composeNotificationFollowup(k);
 if(!result&&!strcmp(context,"message"))result=composeMapNotification(k);
 if(!result&&!strcmp(context,"message"))result=composeCraftNotification(k);
 if(!result&&!strcmp(context,"craft-material"))result=composeCraftMaterialLabel(k);
 if(!result&&!strcmp(context,"showtext"))result=composeCraftPiecesLabel(k);
 if(!result)result=composeMemorial(k,context);
 if(!result)result=composeLook(k,context);
 if(!result&&!strcmp(context,"message"))result=composeMessage(k);
 if(!result&&!strcmp(context,"npc-talk")){
  if(tradePayment)result=composeTradePayment(k,composeItem);
  if(!result)result=composeTradeRejection(k);
  if(!result)result=composeExtraDialogue(k);
 }
 if(!result&&(!strcmp(context,"showtext")||!strcmp(context,"player-talk")))result=composeBlacksmithPlayer(k);
 if(!result)result=matchTemplate(k,@(context));
 if(!result&&drawingItems&&!strcmp(context,"showtext"))result=composeItem(k);
 if(s.capture && s.missing){
  std::string key=[scoped UTF8String];
  if(!s.seen.count(key)&&s.seen.size()<50000){
   NSDictionary* record=@{@"context":@(context),@"original":orig,@"translated":@(result!=nil)};
   NSData* b=[NSJSONSerialization dataWithJSONObject:record options:0 error:nil];
   if(b&&fwrite(b.bytes,1,b.length,s.missing)==b.length&&fputc('\n',s.missing)!=EOF){fflush(s.missing);s.seen.insert(key);}
  }
 }
 return s.enabled?result:nil;
}
struct Bitmap {int w=0,h=0;std::vector<uint8_t> pixels;};
// Rasterize at 2x then let SDL scale to the game's native ten-pixel line grid.
Bitmap raster(NSString* str,int maxWidth,SDL_Color col,CFStringRef face=CFSTR("PingFangSC-Regular")){
 Bitmap b;if(!str.length||maxWidth<8)return b;
 CGFloat size=10;CTFontRef font=CTFontCreateWithName(face,size,nullptr);
 CGColorSpaceRef cs=CGColorSpaceCreateDeviceRGB();CGFloat rgba[]={col.r/255.,col.g/255.,col.b/255.,1};CGColorRef color=CGColorCreate(cs,rgba);
 NSDictionary* attrs=@{(__bridge id)kCTFontAttributeName:(__bridge id)font,(__bridge id)kCTForegroundColorAttributeName:(__bridge id)color};
 NSAttributedString* a=[[NSAttributedString alloc] initWithString:str attributes:attrs];CTLineRef line=CTLineCreateWithAttributedString((__bridge CFAttributedStringRef)a);
 double width=CTLineGetTypographicBounds(line,nullptr,nullptr,nullptr);
 // Short labels may fit to their existing slot; never omit characters.
 double sx=std::min(1.,maxWidth/std::max(1.,width));
 b.w=std::max(1,(int)ceil(std::min((double)maxWidth,width)))*2;b.h=24;
 b.pixels.resize(b.w*b.h*4);
 CGContextRef ctx=CGBitmapContextCreate(b.pixels.data(),b.w,b.h,8,b.w*4,cs,kCGImageAlphaPremultipliedLast|kCGBitmapByteOrder32Big);
 if(ctx){CGContextScaleCTM(ctx,2*sx,2);CGContextSetTextPosition(ctx,0,2);CTLineDraw(line,ctx);CGContextRelease(ctx);}
 for(size_t i=0;i<b.pixels.size();i+=4){auto alpha=b.pixels[i+3];if(alpha)for(int c=0;c<3;c++)b.pixels[i+c]=std::min(255,(int)b.pixels[i+c]*255/alpha);}
 CFRelease(line);CFRelease(font);CGColorRelease(color);CGColorSpaceRelease(cs);return b;
}
std::map<std::string,Bitmap>& cache(){static auto* c=new std::map<std::string,Bitmap>;return *c;}
const Bitmap& bitmap(NSString* str,int width,SDL_Color color){
 auto& c=cache();std::string key=std::string(str.UTF8String)+":"+std::to_string(width)+":"+std::to_string(color.r)+":"+std::to_string(color.g)+":"+std::to_string(color.b);
 auto it=c.find(key);if(it!=c.end())return it->second;if(c.size()>2048)c.clear();return c.emplace(key,raster(str,width,color)).first->second;
}
SDL_Surface* surface(const Bitmap& b){if(!b.w)return nullptr;auto* s=SDL_CreateRGBSurfaceFrom((void*)b.pixels.data(),b.w,b.h,32,b.w*4,0xff,0xff00,0xff0000,0xff000000);if(s)SDL_SetSurfaceBlendMode(s,1);return s;}
bool render(SDL_Renderer* renderer,int x,int y,NSString* translated,SDL_Color color,unsigned flags,int slot){
 if(!renderer||!translated)return false;
 int w=800,h=600;auto* target=SDL_GetRenderTarget(renderer);if(target)SDL_QueryTexture(target,nullptr,nullptr,&w,&h);else SDL_GetRendererOutputSize(renderer,&w,&h);
 int width=std::min(std::max(16,slot),std::max(0,800-x));
 const auto& b=bitmap(translated,width,color);auto* surf=surface(b);if(!surf)return false;
 auto* tex=SDL_CreateTextureFromSurface(renderer,surf);SDL_FreeSurface(surf);if(!tex)return false;
 SDL_SetTextureBlendMode(tex,1);SDL_Rect dst{x,y-1,b.w/2,b.h/2};if(flags)state().convert(&dst);
 bool ok=SDL_RenderCopy(renderer,tex,nullptr,&dst)==0;SDL_DestroyTexture(tex);return ok;
}
bool drawSurface(int x,int y,NSString* translated,uint32_t color,int slot){
 auto* screen=*state().screen;if(!screen||!translated)return false;SDL_Color col{255,255,255,255};SDL_GetRGB(color,screen->format,&col.r,&col.g,&col.b);
 const auto& b=bitmap(translated,std::min(std::max(16,slot),std::max(0,screen->w-x)),col);
 // Software path needs a native-resolution raster, SDL_UpperBlit does not scale.
 if(!b.w)return false;Bitmap small;small.w=b.w/2;small.h=b.h/2;small.pixels.resize(small.w*small.h*4);
 for(int yy=0;yy<small.h;yy++)for(int xx=0;xx<small.w;xx++)for(int ch=0;ch<4;ch++){
  int sum=0;for(int j=0;j<2;j++)for(int i=0;i<2;i++)sum+=b.pixels[((yy*2+j)*b.w+xx*2+i)*4+ch];small.pixels[(yy*small.w+xx)*4+ch]=sum/4;
 }
 auto* src=surface(small);if(!src)return false;SDL_Rect dst{x,y-1,small.w,small.h};bool ok=SDL_UpperBlit(src,nullptr,screen,&dst)==0;SDL_FreeSurface(src);return ok;
}
NSArray* segments(const char* text,const char* context){
 return state().segmented[[NSString stringWithFormat:@"%s\t%@",context,normalize(decode(text))]];
}
bool drawTranslated(int x,int y,NSString* z,uint32_t color,int width,const char* text,const char* context){
 NSArray* parts=segments(text,context);if(!parts)return drawSurface(x,y,z,color,width);
 for(NSDictionary* part in parts)if(!drawSurface(x+[part[@"offset"] intValue],y,part[@"text"],color,[part[@"width"] intValue]))return false;
 return true;
}
bool renderTranslated(SDL_Renderer*r,int x,int y,NSString*z,SDL_Color color,unsigned flags,int width,const char*text,const char*context){
 NSArray* parts=segments(text,context);if(!parts)return render(r,x,y,z,color,flags,width);
 for(NSDictionary* part in parts)if(!render(r,x+[part[@"offset"] intValue],y,part[@"text"],color,flags,[part[@"width"] intValue]))return false;
 return true;
}
template<typename T>T original(const char* key){return reinterpret_cast<T>(state().hooks.at(key).original);}
#include "look_popup.inc"
#include "held_items.inc"
#include "status_text.inc"
#include "encyclopedia_preview.inc"
struct NoteFrame {NSString* translated=nil;bool checked=false;bool painted=false;bool groundItems=false;};
thread_local NoteFrame* activeNote=nullptr;
void captureNote(char* text);
bool prepareNote(int x,int y,unsigned color);
void inventoryEntry(int key,int x,int y,char* text){
 // This call site is validated alongside the executable and entry prologues.
 inventoryList=(uintptr_t)__builtin_return_address(0)==0x1000693e7ULL+_dyld_get_image_vmaddr_slide(0);
 bool previous=drawingItems;drawingItems=inventoryList;
 original<void(*)(int,int,int,char*)>("inventory_entry")(key,x,y,text);drawingItems=previous;
}
void drawList(){bool previous=drawingItems;drawingItems=inventoryList;original<void(*)()>("list_draw")();drawingItems=previous;}
void noteBottom(){original<void(*)()>("note_bottom")();}
using Software=void(*)(int,int,char*,unsigned,int);
using Text=void(*)(int,int,char*);
using Renderer=void(*)(SDL_Renderer*,int,int,char*,SDL_Color,unsigned);
using Texture=void(*)(SDL_Texture*,int,int,char*,SDL_Color,unsigned);
using Asc=void(*)(int,int,uint8_t);
using RenAsc=void(*)(SDL_Renderer*,int,int,uint8_t,int,int,int,unsigned);
void asc(int x,int y,uint8_t c){if(!suppress)original<Asc>("asc")(x,y,c);}
void renasc(SDL_Renderer*r,int x,int y,uint8_t c,int a,int b,int d,unsigned f){if(!suppress)original<RenAsc>("renasc")(r,x,y,c,a,b,d,f);}
void newasc(SDL_Renderer*r,int x,int y,uint8_t c,int a,int b,int d,unsigned f){if(!suppress)original<RenAsc>("newasc")(r,x,y,c,a,b,d,f);}
struct Scope {bool prev;Scope():prev(suppress){++depth;}~Scope(){--depth;suppress=prev;}};
#include "armor_button.inc"
extern thread_local bool inMessageLog;
#include "location_extra.inc"
#include "memorial.inc"
int slot(const char* t){return (int)strcspn(t,"\n")*8;}
void show(int x,int y,char*t,unsigned c,int f){@autoreleasepool{
 auto fn=original<Software>("show");if(depth||!t){fn(x,y,t,c,f);return;}Scope scope;
 if(prepareNote(x,y,c)){suppress=true;fn(x,y,t,c,f);return;}
 if(prepareArmorButton(x,y,t,c)){suppress=true;fn(x,y,t,c,f);return;}
 // A rejected full Note must retain every original fragment. Generic word
 // translations can overpaint neighbouring words and historical row bands.
 if(activeNote){fn(x,y,t,c,f);return;}
 const uintptr_t showCaller=(uintptr_t)__builtin_return_address(0)-_dyld_get_image_vmaddr_slide(0);
 auto z=previewTranslation(x,y);
 if(!z&&state().enabled&&showCaller==0x10010b50cULL)z=memorialCauseCaption(normalize(decode(t)));
 if(!z&&showCaller==0x100150005ULL)z=translate(t,"course-key-conjunction");
 if(!z&&showCaller==0x10005de4cULL)z=translate(t,"inventory-action");
 if(!z&&showCaller==0x10007e0fcULL)z=translate(t,"craft-material");
 if(!z&&statusTextContext)z=translate(t,statusTextContext);
 if(!z&&inMessageLog)z=translate(t,"message-log-ui");if(!z)z=translate(t,"showtext");
 int xx=x==-1?*state().x:x,yy=y==-1?*state().y:y;suppress=z!=nil;fn(x,y,t,c,f);suppress=scope.prev;
 uintptr_t caller=(uintptr_t)__builtin_return_address(0)-_dyld_get_image_vmaddr_slide(0);
 if(z&&(caller==0x10016a201ULL||caller==0x10016a242ULL)){
  SDL_Color rgb{255,255,255,255};SDL_GetRGB(c,(*state().screen)->format,&rgb.r,&rgb.g,&rgb.b);
  xx+=(slot(t)-bitmap(z,slot(t),rgb).w/2)/2;
 }
 if(z&&!drawTranslated(xx,yy,z,c,slot(t),t,"showtext"))fn(x,y,t,c,f);
}}
void text(int x,int y,char*t){@autoreleasepool{
 auto fn=original<Text>("text");if(depth||!t){fn(x,y,t);return;}Scope scope;auto z=translate(t,"textput");uint32_t c=*state().color;suppress=z!=nil;fn(x,y,t);suppress=scope.prev;
 if(z&&!drawSurface(x,y,z,c,slot(t)))fn(x,y,t);
}}
void runRenderer(const char* key,SDL_Renderer*r,int x,int y,char*t,SDL_Color c,unsigned f,bool heading=false){@autoreleasepool{
 auto fn=original<Renderer>(key);if(depth||!t){fn(r,x,y,t,c,f);return;}Scope scope;auto z=previewTranslation(x,y);if(!z)z=translate(t,key);int xx=x==-1?*state().x:x,yy=y==-1?*state().y:y;
 suppress=z!=nil;fn(r,x,y,t,c,f);suppress=scope.prev;
 if(z&&heading&&state().headingBox){int w=state().headingBox->w-10;xx=5+(w-bitmap(z,w,c).w/2)/2;}
 if(z&&!renderTranslated(r,xx,yy,z,c,strcmp(key,"renshow")==0?0:f,slot(t),t,key))fn(r,x,y,t,c,f);
}}
void renshow(SDL_Renderer*r,int x,int y,char*t,SDL_Color c,unsigned f){bool heading=(uintptr_t)__builtin_return_address(0)==0x100131a64ULL+_dyld_get_image_vmaddr_slide(0);runRenderer("renshow",r,x,y,t,c,f,heading);}
void rentext(SDL_Renderer*r,int x,int y,char*t,SDL_Color c,unsigned f){runRenderer("rentext",r,x,y,t,c,f);}
void newtext(SDL_Renderer*r,int x,int y,char*t,SDL_Color c,unsigned f){runRenderer("newtext",r,x,y,t,c,f);}
void newshow(SDL_Texture* target,int x,int y,char*t,SDL_Color c,unsigned f){@autoreleasepool{
 auto fn=original<Texture>("newshow");if(depth||!t){fn(target,x,y,t,c,f);return;}Scope scope;auto z=previewTranslation(x,y);if(!z)z=translate(t,"newshow");if(!z&&state().enabled)z=translateMapTerrainCaption(t);suppress=z!=nil;fn(target,x,y,t,c,f);suppress=scope.prev;
 if(z){auto* r=*state().ren;auto* old=SDL_GetRenderTarget(r);SDL_SetRenderTarget(r,target);bool ok=render(r,x,y,z,c,1,slot(t));SDL_SetRenderTarget(r,old);if(!ok)fn(target,x,y,t,c,f);}
}}
NSString* paragraphSource(){
 NSMutableString* out=[NSMutableString new];char* words=state().words;
 for(int i=0;i<5000;i++){const char* w=words+i*130;size_t n=strnlen(w,130);if(!n)break;if(n==130)return nil;
  if(out.length&&w[0]!='.') [out appendString:@" "];
  [out appendString:decode(w)];
 }return out;
}
struct Run {NSString* text;SDL_Color color;int x,y,w;};
struct Paragraph {std::vector<Run> runs;int height=0;int lastX=0;};
Paragraph layoutParagraph(NSString* text,int width,SDL_Color initial){
 Paragraph out;if(width<10)return out;
 CTFontRef font=CTFontCreateWithName(CFSTR("PingFangSC-Regular"),10,nullptr);
 NSMutableAttributedString* a=[[NSMutableAttributedString alloc] initWithString:@""];
 SDL_Color color=initial;
 NSRegularExpression* tags=[NSRegularExpression regularExpressionWithPattern:@"<[^>]+>" options:0 error:nil];
 NSUInteger cursor=0;
 auto append=[&](NSString* str){uint32_t rgba=color.r|(color.g<<8)|(color.b<<16);NSDictionary* attrs=@{(__bridge id)kCTFontAttributeName:(__bridge id)font,@"urwColor":@(rgba)};[a appendAttributedString:[[NSAttributedString alloc] initWithString:str attributes:attrs]];};
 for(NSTextCheckingResult* match in [tags matchesInString:text options:0 range:NSMakeRange(0,text.length)]){
  append([text substringWithRange:NSMakeRange(cursor,match.range.location-cursor)]);
  NSString* tag=[text substringWithRange:match.range];
  if([tag isEqual:@"<br>"])append(@"\n");
  else if([tag hasPrefix:@"</"])color=initial;
  else if([tag isEqual:@"<red>"])color={168,0,0,255};
  else if([tag isEqual:@"<green>"])color={0,168,0,255};
  else if([tag isEqual:@"<blue>"])color={0,0,255,255};
  else if([tag isEqual:@"<lightgray>"])color={171,171,171,255};
  else if([tag isEqual:@"<black>"])color={0,0,0,255};
  else append(tag);
  cursor=NSMaxRange(match.range);
 }append([text substringFromIndex:cursor]);
 CTTypesetterRef ts=CTTypesetterCreateWithAttributedString((__bridge CFAttributedStringRef)a);
 CFIndex start=0;int y=0;
 while(start<(CFIndex)a.length){
  CFIndex count=CTTypesetterSuggestLineBreak(ts,start,width);if(count<=0)count=1;
  NSRange lineRange=NSMakeRange(start,count);int x=0;
  NSUInteger pos=start;
  while(pos<NSMaxRange(lineRange)){
   NSRange range;NSNumber* val=[a attribute:@"urwColor" atIndex:pos longestEffectiveRange:&range inRange:lineRange];
   NSString* str=[[a.string substringWithRange:range] stringByReplacingOccurrencesOfString:@"\n" withString:@""];
   NSAttributedString* part=[a attributedSubstringFromRange:range];CTLineRef line=CTLineCreateWithAttributedString((__bridge CFAttributedStringRef)part);
   int w=(int)ceil(CTLineGetTypographicBounds(line,nullptr,nullptr,nullptr));CFRelease(line);uint32_t v=val.unsignedIntValue;
   if(str.length)out.runs.push_back({str,{(uint8_t)v,(uint8_t)(v>>8),(uint8_t)(v>>16),255},x,y,w});x+=w;pos=NSMaxRange(range);
  }
  out.lastX=x;start+=count;y+=12;
 }out.height=y;CFRelease(ts);CFRelease(font);return out;
}
// Fit the actual ink, not the 12px line box, into the native 10px row.
// Area averaging preserves strokes that nearest-neighbour subsampling drops.
Bitmap messageRowRaster(NSString* text,SDL_Color c,int width,int height,bool binary,bool fitWidth=false){
 Bitmap row;if(height<8||height>24||width<8)return row;
 const auto b=raster(text,fitWidth?width:4096,c,CFSTR("PingFangSC-Medium"));
 if(!b.w||b.w/2>width)return row;
 int top=b.h,bottom=0;
 for(int yy=0;yy<b.h;yy++)for(int xx=0;xx<b.w;xx++)if(b.pixels[(yy*b.w+xx)*4+3]>8){top=std::min(top,yy);bottom=std::max(bottom,yy+1);}
 if(bottom<=top)return row;
 row.w=b.w/2;row.h=height;row.pixels.resize(row.w*height*4);
 const double scale=(double)(bottom-top)/height;
 for(int yy=0;yy<height;yy++)for(int xx=0;xx<row.w;xx++){
  double start=top+yy*scale,end=top+(yy+1)*scale,coverage=0;
  for(int sy=(int)floor(start);sy<(int)ceil(end);sy++){
   double weight=std::max(0.,std::min(end,(double)sy+1)-std::max(start,(double)sy));
   for(int dx=0;dx<2;dx++)coverage+=weight*b.pixels[(sy*b.w+xx*2+dx)*4+3];
  }
  int alpha=(int)std::lround(coverage/(2*scale));
  size_t i=(yy*row.w+xx)*4;
  row.pixels[i]=c.r;row.pixels[i+1]=c.g;row.pixels[i+2]=c.b;
  // Keep native fade compatible without discarding thin diagonal strokes.
  row.pixels[i+3]=binary?(alpha>=80?255:0):alpha;
 }
 return row;
}
bool drawNoteRow(int x,int y,NSString* text,unsigned color,int width,int height){
 auto* screen=*state().screen;if(!screen)return false;
 SDL_Color c{0,0,0,255};SDL_GetRGB(color,screen->format,&c.r,&c.g,&c.b);
 auto row=messageRowRaster(text,c,width,height,true);
 auto src=surface(row);if(!src)return false;SDL_Rect dst{x,y,row.w,row.h};
 bool ok=SDL_UpperBlit(src,nullptr,screen,&dst)==0;SDL_FreeSurface(src);return ok;
}
bool prepareNote(int x,int y,unsigned color){
 auto* frame=activeNote;auto& s=state();if(!frame||!s.noteBox)return false;
 auto box=*s.noteBox;int row=s.lineHeight(1.0f);
 if(x<box.x+5||x>=box.x+box.w-5||y<box.y+5||y+row>box.y+box.h-5)return false;
 if(!frame->checked){
  frame->checked=true;auto z=translate(s.noteText,"message");
  if(!z&&frame->groundItems&&s.enabled)z=composeItem(normalize(decode(s.noteText)));
  const char* visible=s.noteText;
  if(visible&&*visible&&strchr("!#&+:=>?_@",*visible))++visible;
  // Preserve the native final-answer anchor even when the English source is one row.
  int available=visible?std::min(box.w-10,(int)strlen(visible)*8-8):0;
  if(z&&[z rangeOfCharacterFromSet:[NSCharacterSet newlineCharacterSet]].location==NSNotFound&&![z containsString:@"<"]&&![z containsString:@">"]&&available>=16&&bitmap(z,4096,{0,0,0,255}).w/2<=available)
   frame->translated=z;
 }
 if(!frame->translated)return false;
 if(!frame->painted){
  if(!drawNoteRow(box.x+5,y,frame->translated,color,box.w-10,row)){frame->translated=nil;return false;}
  frame->painted=true;
 }
 return true;
}
void captureNote(char* text){@autoreleasepool{
 NoteFrame frame;auto* previous=activeNote;activeNote=&frame;
 frame.groundItems=(uintptr_t)__builtin_return_address(0)==0x10013dfddULL+_dyld_get_image_vmaddr_slide(0);
 // Native code still owns sound, English buffers, log, MoreCheck and pixel history.
 // Drawing occurs inside its first showtext, before any subsequent scroll or flip.
 original<void(*)(char*)>("note")(text);activeNote=previous;
}}
using Para= int(*)(int,int,int,int,unsigned,int);
#include "message_log.inc"
using RenPara=int(*)(SDL_Renderer*,int,int,int,int,SDL_Color,int);
int paragraph(int x,int y,int width,int height,unsigned color,int flags){@autoreleasepool{
 auto fn=original<Para>("paragraph");if(depth)return fn(x,y,width,height,color,flags);
 const uintptr_t caller=(uintptr_t)__builtin_return_address(0)-_dyld_get_image_vmaddr_slide(0);
 if(caller==0x100135941ULL)return renderMessageLogRecord(fn,x,y,width,height,color,flags);
 auto source=paragraphSource();if(!source)return fn(x,y,width,height,color,flags);
 auto z=translate(source.UTF8String,"paragraph");if(!z){Scope scope;return fn(x,y,width,height,color,flags);}
 auto* screen=*state().screen;SDL_Color col{255,255,255,255};SDL_GetRGB(color,screen->format,&col.r,&col.g,&col.b);
 auto p=layoutParagraph(z,width,col);Scope scope;suppress=true;fn(x,y,width,height,color,flags);suppress=scope.prev;
 if(height!=-1)for(auto& run:p.runs){uint32_t pixel=SDL_MapRGB(screen->format,run.color.r,run.color.g,run.color.b);drawSurface(x+run.x,y+run.y,run.text,pixel,run.w);}
 const int lastRow=std::max(0,p.height-12);
 *state().x=x+p.lastX;*state().y=y+lastRow;
 // NPC_inforuutu adds 35 px to the measured height and draws at y+30.
 // Reserve the complete final row in the portion sent to the renderer.
 return height==-1&&caller==0x1000cf788ULL?p.height:lastRow;
}}
int renparagraph(SDL_Renderer*r,int x,int y,int width,int height,SDL_Color color,int flags){@autoreleasepool{
 auto fn=original<RenPara>("renparagraph");if(depth)return fn(r,x,y,width,height,color,flags);
 auto source=paragraphSource();if(!source)return fn(r,x,y,width,height,color,flags);
 auto z=translate(source.UTF8String,"paragraph");if(!z){Scope scope;return fn(r,x,y,width,height,color,flags);}
 auto p=layoutParagraph(z,width,color);Scope scope;suppress=true;fn(r,x,y,width,height,color,flags);suppress=scope.prev;
 if(height!=-1)for(auto& run:p.runs)render(r,x+run.x,y+run.y,run.text,run.color,0,run.w);
 *state().x=x+p.lastX;*state().y=y+std::max(0,p.height-12);return height==-1?p.height:std::max(0,p.height-12);
}}

#include "hypertext.inc"
void jump(uint8_t* at,void* to){at[0]=0xff;at[1]=0x25;memset(at+2,0,4);memcpy(at+6,&to,8);}
bool writable(void* p,size_t n,bool write){auto page=(uintptr_t)p&~(uintptr_t)(getpagesize()-1);auto end=((uintptr_t)p+n+getpagesize()-1)&~(uintptr_t)(getpagesize()-1);return mach_vm_protect(mach_task_self(),page,end-page,false,write?(VM_PROT_READ|VM_PROT_WRITE|VM_PROT_COPY):(VM_PROT_READ|VM_PROT_EXECUTE))==KERN_SUCCESS;}
void rollback(){for(auto& [key,h]:state().hooks){if(writable(h.address,h.bytes.size(),true)){memcpy(h.address,h.bytes.data(),h.bytes.size());writable(h.address,h.bytes.size(),false);}}}
bool install(NSDictionary* bindings){
 intptr_t slide=_dyld_get_image_vmaddr_slide(0);
 std::map<std::string,void*> replacements={{"note",(void*)&captureNote},{"paragraph",(void*)&paragraph},{"renparagraph",(void*)&renparagraph},{"show",(void*)&show},{"text",(void*)&text},{"renshow",(void*)&renshow},{"rentext",(void*)&rentext},{"newtext",(void*)&newtext},{"newshow",(void*)&newshow},{"asc",(void*)&asc},{"renasc",(void*)&renasc},{"newasc",(void*)&newasc}};
 NSDictionary* hs=bindings[@"hooks"];
 replacements["note_bottom"]=(void*)&noteBottom;
 replacements["hyper_show"]=(void*)&hyperShow;replacements["npc_talk"]=(void*)&npcTalk;replacements["player_talk"]=(void*)&playerTalk;
 replacements["inventory_entry"]=(void*)&inventoryEntry;replacements["list_draw"]=(void*)&drawList;
 replacements["held_item_bar"]=(void*)&heldItemBar;
 replacements["centered_text"]=(void*)&centeredText;
 replacements["armor_button"]=(void*)&armorButton;
 replacements["status_text_box"]=(void*)&statusTextBox;
 replacements["choose_culture"]=(void*)&chooseCulture;
 replacements["game_info_preview"]=(void*)&gameInfoPreview;
 replacements["texture_info_preview"]=(void*)&textureInfoPreview;
 replacements["flip_screen_portion"]=(void*)&flipScreenPortion;
 replacements["message_log"]=(void*)&messageLog;replacements["message_log_words"]=(void*)&messageLogWords;
 NSDictionary* gs=bindings[@"global_symbols"];
 for(NSString* key in gs){
  NSString* symbol=gs[key];if(![symbol isKindOfClass:[NSString class]]||symbol.length<2)return false;
  void* address=dlsym(RTLD_DEFAULT,symbol.UTF8String+1);
  if(!address||(uintptr_t)address!=[bindings[@"globals"][key] unsignedLongLongValue]+slide)return false;
 }
 // Validate every hook before changing any instruction.
 for(auto& [key,replacement]:replacements){NSDictionary* h=hs[@(key.c_str())];if(![h isKindOfClass:[NSDictionary class]])return false;uintptr_t address=[h[@"address"] unsignedLongLongValue]+slide;NSString* hex=h[@"bytes"],*symbol=h[@"symbol"];std::vector<uint8_t> bytes;
  if(![hex isKindOfClass:[NSString class]]||hex.length<28||hex.length>64||hex.length%2||![symbol isKindOfClass:[NSString class]]||symbol.length<2)return false;
  void* sym=dlsym(RTLD_DEFAULT,symbol.UTF8String+1);if(!sym||sym!=(void*)address)return false;
  for(NSUInteger i=0;i<hex.length;i+=2){unsigned value=0;[[NSScanner scannerWithString:[hex substringWithRange:NSMakeRange(i,2)]] scanHexInt:&value];bytes.push_back(value);}
  if(bytes.size()<14||memcmp((void*)address,bytes.data(),bytes.size()))return false;
 }
 for(auto& [key,replacement]:replacements){NSDictionary* h=hs[@(key.c_str())];uintptr_t address=[h[@"address"] unsignedLongLongValue]+slide;NSString* hex=h[@"bytes"];size_t n=hex.length/2;std::vector<uint8_t> bytes(n);memcpy(bytes.data(),(void*)address,n);
  auto* trampoline=(uint8_t*)mmap(nullptr,4096,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0);if(trampoline==MAP_FAILED){rollback();return false;}
  memcpy(trampoline,bytes.data(),n);jump(trampoline+n,(void*)(address+n));if(mprotect(trampoline,4096,PROT_READ|PROT_EXEC)){munmap(trampoline,4096);rollback();return false;}
  state().hooks.emplace(key,Hook{(void*)address,trampoline,bytes});
  if(!writable((void*)address,n,true)){rollback();return false;}jump((uint8_t*)address,replacement);memset((uint8_t*)address+14,0x90,n-14);
  if(!writable((void*)address,n,false)){rollback();return false;}
 }
 NSDictionary* g=bindings[@"globals"];auto addr=[&](NSString*k){return [g[k] unsignedLongLongValue]+slide;};
 auto& s=state();
 s.messageLogText=(char*)addr(@"message_log_text");s.messageLogFormat=(char*)addr(@"message_log_format");
 s.headingBox=(SDL_Rect*)addr(@"heading_box");
 s.screenTexture=(SDL_Texture**)addr(@"screen_texture");
 s.hyperX=(int*)addr(@"hyper_x");s.hyperY=(int*)addr(@"hyper_y");s.hyperLine=(int*)addr(@"hyper_line");s.linkPos=(int*)addr(@"link_pos");s.linkList=(char*)addr(@"link_list");s.topics=(char*)addr(@"topics");
 s.npcX=(int*)addr(@"npc_x");s.npcY=(int*)addr(@"npc_y");s.playerX=(int*)addr(@"player_x");s.playerY=(int*)addr(@"player_y");s.spotEntry=(void(*)(int,int,int,int,int))addr(@"spot_entry");s.line=(void(*)(int,int,int,int))addr(@"line");s.flip=(void(*)())addr(@"flip");
 s.noteText=(char*)addr(@"note");s.noteBox=(SDL_Rect*)addr(@"notebox");s.lineHeight=(int(*)(float))addr(@"textlineh");s.flipMap=(void(*)())addr(@"flipmap");s.words=(char*)addr(@"words");s.screen=(SDL_Surface**)addr(@"screen");s.ren=(SDL_Renderer**)addr(@"ren");s.color=(uint32_t*)addr(@"color");s.x=(int*)addr(@"x");s.y=(int*)addr(@"y");s.convert=(void(*)(SDL_Rect*))addr(@"convert");return true;
}
void loadCatalog(){
 state().itemRules=checkedItemRules(json([base() stringByAppendingPathComponent:@"data/items.json"]));
 NSMutableDictionary* dictionary=[NSMutableDictionary new];NSMutableDictionary* segmented=[NSMutableDictionary new];NSMutableArray* templates=[NSMutableArray new];
 NSString* catalogPath=[base() stringByAppendingPathComponent:@"data/translations"];
 NSRegularExpression* params=[NSRegularExpression regularExpressionWithPattern:@"\\{([A-Za-z][A-Za-z0-9_]*):(int|number|text)\\}" options:0 error:nil];
 for(NSString* name in [[[NSFileManager defaultManager] contentsOfDirectoryAtPath:catalogPath error:nil] sortedArrayUsingSelector:@selector(compare:)]){if(![name hasSuffix:@".json"])continue;id rows=json([catalogPath stringByAppendingPathComponent:name]);if(![rows isKindOfClass:[NSArray class]])continue;
  for(id e in rows){if(![e isKindOfClass:[NSDictionary class]]||![e[@"status"] isEqual:@"reviewed"])continue;
   NSString* z=e[@"translation"],*src=e[@"original"],*context=e[@"context"];
   if(![z isKindOfClass:[NSString class]]||!z.length||![src isKindOfClass:[NSString class]]||![context isKindOfClass:[NSString class]])continue;
   if([z isEqual:src])continue; // Keep original keycaps, numeric fields and bitmap symbols.
   NSString* k=normalize(src);id parts=e[@"segments"];
   if(parts){
    bool valid=[parts isKindOfClass:[NSArray class]]&&[parts count]>0&&[parts count]<=16&&([context isEqual:@"showtext"]||[context isEqual:@"renshow"]);
    int end=0;NSMutableString* combined=[NSMutableString new];
    if(valid)for(id part in parts){
     if(![part isKindOfClass:[NSDictionary class]]||![part[@"text"] isKindOfClass:[NSString class]]||![part[@"text"] length]||![part[@"offset"] isKindOfClass:[NSNumber class]]||![part[@"width"] isKindOfClass:[NSNumber class]]){valid=false;break;}
     int offset=[part[@"offset"] intValue],width=[part[@"width"] intValue];
     if(offset<end||width<16||offset+width>(int)src.length*8){valid=false;break;}
     end=offset+width;[combined appendString:part[@"text"]];
    }
    if(!valid||![normalize(combined) isEqual:normalize(z)]||[e[@"kind"] isEqual:@"template"])continue;
    segmented[[NSString stringWithFormat:@"%@\t%@",context,k]]=parts;
   }
   if([e[@"kind"] isEqual:@"template"]){
    if(!context.length||[context isEqual:@"*"])continue;
    NSMutableString* pattern=[NSMutableString stringWithString:@"\\A"];NSMutableArray* names=[NSMutableArray new];NSUInteger cursor=0;
    for(NSTextCheckingResult* m in [params matchesInString:k options:0 range:NSMakeRange(0,k.length)]){
     [pattern appendString:[NSRegularExpression escapedPatternForString:[k substringWithRange:NSMakeRange(cursor,m.range.location-cursor)]]];
     NSString* type=[k substringWithRange:[m rangeAtIndex:2]];
     [pattern appendString:[type isEqual:@"int"]?@"([0-9]+)":[type isEqual:@"number"]?@"([+-]?[0-9]+(?:[.][0-9]+)?)":@"([^\\r\\n]{1,256}?)"];
     [names addObject:[k substringWithRange:[m rangeAtIndex:1]]];cursor=NSMaxRange(m.range);
    }
    [pattern appendString:[NSRegularExpression escapedPatternForString:[k substringFromIndex:cursor]]];[pattern appendString:@"\\z"];
    NSRegularExpression* regex=[NSRegularExpression regularExpressionWithPattern:pattern options:0 error:nil];
    if(regex&&names.count)[templates addObject:@{@"context":context,@"translation":z,@"regex":regex,@"names":names}];
   }else{
    if([e[@"allow_break_variation"] boolValue]&&[context isEqual:@"paragraph"])dictionary[[@"paragraph-prose\t" stringByAppendingString:proseKey(src)]]=z;
    if(context.length&&![context isEqual:@"*"])k=[NSString stringWithFormat:@"%@\t%@",context,k];dictionary[k]=z;}
  }
 }
 state().dictionary=dictionary;state().templates=templates;state().segmented=segmented;
}
#ifndef URW_ZH_TEST
__attribute__((constructor)) void start(){@autoreleasepool{
 auto& s=state();NSString* root=base();NSString* logdir=[root stringByAppendingPathComponent:@"logs"];[[NSFileManager defaultManager] createDirectoryAtPath:logdir withIntermediateDirectories:YES attributes:nil error:nil];s.log=fopen([[logdir stringByAppendingPathComponent:@"runtime.log"] fileSystemRepresentation],"a");
 NSDictionary* bindings=json([root stringByAppendingPathComponent:@"data/bindings.json"]);NSData* executable=[NSData dataWithContentsOfFile:@(_dyld_get_image_name(0))];
 if(!bindings||!executable){note("disabled: missing bindings or executable");return;}unsigned char digest[CC_SHA256_DIGEST_LENGTH];CC_SHA256(executable.bytes,(CC_LONG)executable.length,digest);NSMutableString* hash=[NSMutableString new];for(auto b:digest)[hash appendFormat:@"%02x",b];
 if(![hash isEqual:bindings[@"sha256"]]){note("disabled: unsupported executable SHA-256");return;}
 s.config=json([root stringByAppendingPathComponent:@"data/config.json"]);s.enabled=s.config[@"enabled"]?[s.config[@"enabled"] boolValue]:true;s.capture=s.config[@"capture"]?[s.config[@"capture"] boolValue]:true;
 loadCatalog();s.missing=fopen([[logdir stringByAppendingPathComponent:@"captured.jsonl"] fileSystemRepresentation],"a");
 if(!install(bindings)){note("disabled: symbol, instruction, or memory protection validation failed");return;}
 note([[NSString stringWithFormat:@"ready: 3.89.1 x86_64; %lu translations; enabled=%d",(unsigned long)s.dictionary.count,s.enabled] UTF8String]);
}}
#endif
}

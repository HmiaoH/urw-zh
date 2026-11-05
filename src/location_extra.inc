// These entries are only valid at terrain display sites.
NSString* translateTerrainName(NSString* source){
 if(!source.length)return nil;
 return state().dictionary[[@"terrain-name\t" stringByAppendingString:source]];
}

NSString* translateMapTerrainCaption(const char* text){
 // SlaveRender passes the caption field at +0x840 in a fixed array of 128 slots.
 // Only the "regstat_terrain" slot receives the name from karttapaikka_teksti.
 constexpr uintptr_t stride=0xc50, captionOffset=0x840;
 static auto* slots=(const char*)dlsym(RTLD_DEFAULT,"SlaveScreen");
 if(!slots||!text)return nil;
 uintptr_t address=(uintptr_t)text, first=(uintptr_t)slots+captionOffset;
 if(address<first||address-first>=128*stride||(address-first)%stride)return nil;
 const char* name=slots+(address-first)+8;
 if(memcmp(name,"regstat_terrain",sizeof("regstat_terrain")))return nil;
 refreshConfig();
 return state().enabled?translateTerrainName(decode(text)):nil;
}

#include "map_names.inc"

NSString* translateMapLocation(NSString* source){
 if(!source.length)return nil;
 if(NSString* terrain=translateTerrainName(source))return terrain;

 // Region titles can add one pair of quotes around the entire map label.
 bool quoted=[source hasPrefix:@"\""]&&[source hasSuffix:@"\"\""];
 NSString* location=quoted?[source substringWithRange:NSMakeRange(1,source.length-2)]:source;
 NSRange at=[location rangeOfString:@" at "];
 NSString* terrain=nil;
 if(at.location!=NSNotFound){
  terrain=translateTerrainName([location substringToIndex:at.location]);
  if(!terrain)return nil;
  location=[location substringFromIndex:NSMaxRange(at)];
 }

 // Translate only the quoted English gloss. Keep the Finnish name as supplied.
 NSRange gloss=[location rangeOfString:@" \""];
 if(gloss.location==NSNotFound||gloss.location==0||![location hasSuffix:@"\""]||
    location.length<=NSMaxRange(gloss))return nil;
 if(NSString* z=translateQuotedMapGloss([location substringFromIndex:gloss.location+1])){
  location=[NSString stringWithFormat:@"%@ %@",[location substringToIndex:gloss.location],z];
 }else if(!terrain)return nil;
 if(terrain)location=[NSString stringWithFormat:@"%@ · %@",location,terrain];
 return quoted?[NSString stringWithFormat:@"\"%@\"",location]:location;
}

void centeredText(int x,int y,int width,char* text,unsigned color,int flags){@autoreleasepool{
 auto fn=original<void(*)(int,int,int,char*,unsigned,int)>("centered_text");

 if(depth||width<16||!text){
  fn(x,y,width,text,color,flags);
  return;
 }
 refreshConfig();
 NSString* z=nullptr;
 if(state().enabled){
  const uintptr_t caller=(uintptr_t)__builtin_return_address(0)-_dyld_get_image_vmaddr_slide(0);
  if(caller==0x1000ab213ULL)z=translateQuotedMapGloss(decode(text));
  if(caller==0x1000ab264ULL||caller==0x1000ab3d9ULL)z=translateMapLocation(decode(text));
  if(caller==0x1000ab2b1ULL)z=translateMapRegion(decode(text));
 }
 if(!z)z=translate(text,"showtext");
 auto* screen=state().screen?*state().screen:nullptr;
 if(!z||!screen){
  fn(x,y,width,text,color,flags);
  return;
 }
 SDL_Color rgb{255,255,255,255};
 SDL_GetRGB(color,screen->format,&rgb.r,&rgb.g,&rgb.b);
 int translatedWidth=bitmap(z,width,rgb).w/2;
 Scope scope;
 suppress=true;
 fn(x,y,width,text,color,flags);
 suppress=scope.prev;
 if(!drawSurface(x+(width-translatedWidth)/2,y,z,color,width))fn(x,y,width,text,color,flags);
}}

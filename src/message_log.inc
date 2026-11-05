// MsgLog parses the saved file itself and keeps its English ring buffers.
// Use the metadata's original Note byte for lookup, then paint within the
// record's native footprint so the next record and the page indices stay put.
thread_local bool inMessageLog=false;
struct MessageLogRecord {const char* text=nullptr;const char* format=nullptr;};
thread_local MessageLogRecord messageLogRecord;
extern "C" int SDL_UpperBlitScaled(SDL_Surface*,const SDL_Rect*,SDL_Surface*,SDL_Rect*);

void messageLog(){@autoreleasepool{
 bool previous=inMessageLog;
 inMessageLog=true;
 original<void(*)()>("message_log")();
 messageLogRecord={};
 inMessageLog=previous;
}}

void messageLogWords(int reset,char* text){
 constexpr uintptr_t recordReturn=0x100135ad6ULL;
 if(inMessageLog&&reset&&
    (uintptr_t)__builtin_return_address(0)==recordReturn+_dyld_get_image_vmaddr_slide(0)){
  messageLogRecord={};
  auto& s=state();
  uintptr_t offset=(uintptr_t)text-(uintptr_t)s.messageLogText;
  if(offset<70*1024&&offset%1024==0)
   messageLogRecord={text,s.messageLogFormat+offset/1024*100};
 }
 original<void(*)(int,char*)>("message_log_words")(reset,text);
}

NSString* messageLogKey(const char* text,const char* format){
 if(!text||!*text||!format||strnlen(format,17)<17||
    format[0]!='('||format[7]!=')'||format[8]!=':'||format[13]!=':'||
    format[14]!='['||format[16]!=']')return nil;
 char prefix=format[15];
 // The log's manual entry command writes the marker ["] and its own text.
 if(prefix=='"')return nil;
 NSString* source=decode(text);
 if(strchr("!#&+:=>?_@",prefix))return [NSString stringWithFormat:@"%c%@",prefix,source];
 return source;
}

NSString* translateMessageLogRecord(MessageLogRecord record){
 NSString* key=messageLogKey(record.text,record.format);
 if(!key)return nil;
 refreshConfig();
 if(!state().enabled)return nil;
 // A bare inventory line retains its first byte and uses black ink. The
 // item parser matches the whole name, including quantity and qualifiers.
 if(!memcmp(record.format,"(000000)",8)&&record.format[15]==*record.text)
  if(NSString* item=composeItem(normalize(key)))return item;
 return translate(key.UTF8String,"message");
}

std::vector<NSString*> messageLogLines(NSString* text,int width,int maxRows){
 text=proseKey(text);
 if(maxRows==1)return {text};
 CTFontRef font=CTFontCreateWithName(CFSTR("PingFangSC-Regular"),10,nullptr);
 NSAttributedString* attributed=[[NSAttributedString alloc] initWithString:text attributes:@{(__bridge id)kCTFontAttributeName:(__bridge id)font}];
 CTTypesetterRef typesetter=CTTypesetterCreateWithAttributedString((__bridge CFAttributedStringRef)attributed);
 CFRelease(font);
 std::vector<NSString*> lines;
 // Prefer normal-width wrapping. If the translation takes more space than
 // the source, widen the wrap measure and fit the complete lines horizontally.
 for(double measure=width;;measure*=1.25){
  lines.clear();
  CFIndex offset=0;
  while(offset<(CFIndex)text.length&&(int)lines.size()<maxRows){
   CFIndex count=CTTypesetterSuggestLineBreak(typesetter,offset,measure);
   if(count<=0)count=[text rangeOfComposedCharacterSequenceAtIndex:offset].length;
   lines.push_back([text substringWithRange:NSMakeRange(offset,count)]);
   offset+=count;
  }
  if(offset==(CFIndex)text.length)break;
 }
 CFRelease(typesetter);
 return lines;
}

int renderMessageLogRecord(Para fn,int x,int y,int width,int height,unsigned color,int flags){@autoreleasepool{
 auto record=messageLogRecord;
 messageLogRecord={};
 NSString* translated=inMessageLog?translateMessageLogRecord(record):nil;
 auto* screen=state().screen?*state().screen:nullptr;
 Scope scope;
 if(!translated||!screen||width<16||height<=0)return fn(x,y,width,height,color,flags);

 // With height == -1 native layout computes wrapping without painting.
 int nativeOffset=fn(x,y,width,-1,color,flags);
 int rowHeight=std::min(10,height);
 auto lines=messageLogLines(translated,width,nativeOffset/10+1);
 SDL_Color rgb{0,0,0,255};
 SDL_GetRGB(color,screen->format,&rgb.r,&rgb.g,&rgb.b);
 for(size_t index=0;index<lines.size();++index){
  const auto b=messageRowRaster(lines[index],rgb,width,rowHeight,false,true);
  auto* src=surface(b);
  if(!src)return fn(x,y,width,height,color,flags);
  SDL_Rect dst{x,y+(int)index*10,b.w,rowHeight};
  int result=SDL_UpperBlit(src,nullptr,screen,&dst);
  SDL_FreeSurface(src);
  if(result!=0)return fn(x,y,width,height,color,flags);
 }
 return nativeOffset;
}}

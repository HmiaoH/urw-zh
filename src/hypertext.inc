struct HyperRun {int x,y,w;NSString* text;NSString* target;};
struct HyperLayout {std::vector<HyperRun> runs;int x,y;bool valid=true;};
HyperLayout hyperLayout(NSString* marked,int x,int y,int left=60,int right=741){
 HyperLayout p{{},x,y,true};
 NSRegularExpression* re=[NSRegularExpression regularExpressionWithPattern:@"\\[\\[([A-ZÄÖÅ0-9 / .'-]+)\\|([^\\[\\]\\n]+)\\]\\]" options:0 error:nil];
 NSMutableArray* spans=[NSMutableArray new];NSUInteger cursor=0;
 for(NSTextCheckingResult* m in [re matchesInString:marked options:0 range:NSMakeRange(0,marked.length)]){
  if(m.range.location>cursor)[spans addObject:@{@"text":[marked substringWithRange:NSMakeRange(cursor,m.range.location-cursor)]}];
  [spans addObject:@{@"text":[marked substringWithRange:[m rangeAtIndex:2]],@"target":[marked substringWithRange:[m rangeAtIndex:1]]}];cursor=NSMaxRange(m.range);
 }
 if(cursor<marked.length)[spans addObject:@{@"text":[marked substringFromIndex:cursor]}];
 for(NSDictionary* span in spans){NSString* text=span[@"text"],*target=span[@"target"];
  if([text containsString:@"[["]||[text containsString:@"]]"]){p.valid=false;return p;}
  for(NSUInteger pos=0;pos<text.length;){NSRange range=[text rangeOfComposedCharacterSequenceAtIndex:pos];NSString* c=[text substringWithRange:range];pos=NSMaxRange(range);
   if([c isEqual:@"\n"]){p.x=left;p.y+=12;continue;}
   int width=bitmap(c,100,{0,0,0,255}).w/2;
   if(p.x+width>right){p.x=left;p.y+=12;}
   if(p.y>500||width<=0||width>right-left){p.valid=false;return p;}
   // Merge adjacent characters of the same link; the exact run width defines its hit area.
   if(!p.runs.empty()&&p.runs.back().y==p.y&&p.runs.back().x+p.runs.back().w==p.x&&((!target&&!p.runs.back().target)||[target isEqual:p.runs.back().target])){
    auto& run=p.runs.back();run.text=[run.text stringByAppendingString:c];run.w+=width;
   }else p.runs.push_back({p.x,p.y,width,c,target});
   p.x+=width;
  }
 }return p;
}
NSData* hyperTargetBytes(NSString* target){
 return [target dataUsingEncoding:CFStringConvertEncodingToNSStringEncoding(kCFStringEncodingDOSLatinUS) allowLossyConversion:NO];
}
void hyperShow(char* source,char* excluded){@autoreleasepool{
 auto fn=original<void(*)(char*,char*)>("hyper_show");NSString* decoded=[[NSString alloc] initWithBytes:source length:strlen(source) encoding:CFStringConvertEncodingToNSStringEncoding(kCFStringEncodingDOSLatinUS)];
 auto z=translate(decoded?decoded.UTF8String:source,"encyclopedia");
 if(!z){Scope scope;fn(source,excluded);return;}
 auto& s=state();auto p=hyperLayout([z stringByReplacingOccurrencesOfString:@"<br>" withString:@"\n"],*s.hyperX,*s.hyperY);
 int links=0;for(auto& r:p.runs)if(r.target){++links;bool known=false;NSData* bytes=hyperTargetBytes(r.target);
  for(int i=0;i<1000;i++)if(bytes && bytes.length<200 && strlen(s.topics+i*200)==bytes.length && !memcmp(s.topics+i*200,bytes.bytes,bytes.length)){known=true;break;}
  if(!known||r.target.length>=200)p.valid=false;
 }
 if(!p.valid||*s.linkPos<0||*s.linkPos+links>=99){Scope scope;fn(source,excluded);return;}
 auto screen=*s.screen;
 for(auto& r:p.runs){auto color=r.target?SDL_MapRGB(screen->format,60,90,152):SDL_MapRGB(screen->format,0,0,0);
  drawSurface(r.x,r.y,r.text,color,r.w);
  if(r.target){NSData* bytes=hyperTargetBytes(r.target);memcpy(s.linkList+(*s.linkPos)*200,bytes.bytes,bytes.length);s.linkList[(*s.linkPos)*200+bytes.length]=0;s.spotEntry(0,r.x-2,r.y-3,r.w+3,15);++*s.linkPos;
   *s.color=color;s.line(r.x,r.y+8,r.x+r.w,r.y+8);
  }
 }
 *s.hyperX=p.x;*s.hyperY=p.y;*s.hyperLine=p.y;*s.x=p.x;*s.y=p.y;
}}
void talkDisplay(char* source,bool npc,bool tradePayment=false){@autoreleasepool{
 const char* key=npc?"npc_talk":"player_talk";auto fn=original<void(*)(char*)>(key);
 auto z=translate(source,npc?"npc-talk":"player-talk",tradePayment);if(!z){Scope scope;fn(source);return;}
 auto& s=state();int* col=npc?s.npcX:s.playerX;int* row=npc?s.npcY:s.playerY;
 int left=npc?15:175,right=npc?299:458,bottom=npc?415:215;
 auto p=hyperLayout(z,*col,*row,left,right);
 if(!p.valid||p.y+12>bottom){Scope scope;fn(source);return;}
 for(auto& r:p.runs)drawSurface(r.x,r.y,r.text,SDL_MapRGB((*s.screen)->format,0,0,0),r.w);
 *col=p.x+8;*row=p.y;s.flip();
}}
void npcTalk(char* s){
 // npc_trade_suggestion's separate list call. Keep matching within the verified native site.
 const uintptr_t caller=(uintptr_t)__builtin_return_address(0)-_dyld_get_image_vmaddr_slide(0);
 talkDisplay(s,true,caller==0x10018196bULL);
}
void playerTalk(char* s){talkDisplay(s,false);}

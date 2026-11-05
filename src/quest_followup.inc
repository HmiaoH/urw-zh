// Display-only quest prose. Unknown dynamic items retain the original paragraph.
NSString* questSentence(NSString* source){
 NSString* direct=state().dictionary[[@"npc-talk\t" stringByAppendingString:source]];
 if(direct)return direct;
 if(NSString* item=notificationSpan(source,@"If you could bring me ",@" I would be very grateful.")){
  if(NSString* z=composeItem(item))return [NSString stringWithFormat:@"如果你能给我带来%@，我将不胜感激。",z];
 }
 if(NSString* item=notificationSpan(source,@"Oh! You've fetched me all the precious ",@" I wanted! May the spirits smile on you, friend, thank you.")){
  NSString* z=composeItem(item)?:state().dictionary[[@"quest-term\t" stringByAppendingString:item]];
  if(z)return [NSString stringWithFormat:@"哦！你把我想要的珍贵%@全都采来了！愿灵体眷顾你，朋友，谢谢你。",z];
 }
 NSString* name=notificationSpan(source,@"It's an herbal cure I make with the most potent herbs around. I call it ",@" and a dose of it is a handy thing to have on hand if you find yourself in a bad fix in the wilderness. I've never heard anyone complain about its effectiveness in wound treatment, and it makes a healthy herbal beverage too.");
 if(name){NSString* z=state().dictionary[[@"quest-term\t" stringByAppendingString:name]];
  if(z)return [NSString stringWithFormat:@"这是我用这一带药效最强的草药配制的疗方，叫作%@。在荒野陷入困境时，随身带上一剂很有用。从未有人抱怨过它治疗伤口的效果；它也能调制成有益健康的草药饮品。",z];}
 return nil;
}
NSString* composeQuest(NSString* source,const char* context){
 if(!strcmp(context,"npc-talk"))return questSentence(source);
 if(strcmp(context,"paragraph"))return nil;
 // Quest journal constructs one shared word table from quoted records, each
 // followed by two breaks (native 0x1001aafee). Translate before line splitting.
 NSArray* parts=[source componentsSeparatedByString:@"<br>"];
 NSMutableArray* translated=[NSMutableArray new];bool found=false;
 for(NSString* raw in parts){
  NSString* part=normalize(raw);
  if(!part.length){[translated addObject:@""];continue;}
  bool quoted=[part hasPrefix:@"\""]&&[part hasSuffix:@"\""]&&part.length>=2;
  NSString* body=quoted?[part substringWithRange:NSMakeRange(1,part.length-2)]:part;
  NSString* z=questSentence(body);if(!z)return nil;
  found=true;[translated addObject:quoted?[NSString stringWithFormat:@"“%@”",z]:z];
 }
 return found?[translated componentsJoinedByString:@"<br>"]:nil;
}

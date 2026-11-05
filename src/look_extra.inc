thread_local bool drawingProfileUnit=false;

// Native human labels use a culture adjective followed by a role. Keep names
// verbatim and require every descriptive component to be in the reviewed list.
NSString* lookTerm(NSString* group,NSString* value){
 return state().dictionary[[group stringByAppendingString:[value lowercaseString]]];
}
NSString* lookIdentity(NSString* source){
 if(!source.length||source.length>180)return nil;
 NSString* person=nil;
 NSRange named=[source rangeOfString:@" the " options:NSCaseInsensitiveSearch];
 if(named.location!=NSNotFound){
  person=[source substringToIndex:named.location];
  if([person rangeOfString:@"\\A\\p{Lu}[\\p{L}\\p{M}’'-]*(?: \\p{Lu}[\\p{L}\\p{M}’'-]*)*\\z" options:NSRegularExpressionSearch].location==NSNotFound)return nil;
  source=[source substringFromIndex:NSMaxRange(named)];
 }
 NSString* result=lookTerm(@"look-label\t",source);
 if(!result){
  NSString* description=[source lowercaseString];
  NSString* age=@"";
  if([description hasPrefix:@"old "]){
   age=@"年老的";
   description=[description substringFromIndex:4];
  }else if([description hasPrefix:@"young "]){
   age=@"年轻的";
   description=[description substringFromIndex:6];
  }
  NSRange split=[description rangeOfString:@" "];
  if(split.location==NSNotFound)return nil;
  NSString* culture=lookTerm(@"look-culture\t",[description substringToIndex:split.location]);
  NSString* role=lookTerm(@"look-role\t",[description substringFromIndex:NSMaxRange(split)]);
  if(!culture||!role)return nil;
  result=[NSString stringWithFormat:@"%@%@%@",age,culture,role];
 }
 return person?[NSString stringWithFormat:@"%@（%@）",person,result]:result;
}

NSString* lookItem(NSString* source){
 // Verbose indefinite forms add an article for wielded items.
 if([source hasPrefix:@"an "])source=[source substringFromIndex:3];
 else if([source hasPrefix:@"a "])source=[source substringFromIndex:2];
 return composeItem(source);
}
NSString* lookItemList(NSString* source){
 if(!source.length||source.length>2048)return nil;
 if(NSString* item=lookItem(source))return item;

 // The native comma-list formatter leaves commas between entries and adds
 // "and" before the last one. Every entry must match the full item grammar.
 source=[source stringByReplacingOccurrencesOfString:@", and " withString:@" and "];
 NSArray<NSString*>* ends=[source componentsSeparatedByString:@" and "];
 if(ends.count!=2)return nil;
 NSArray<NSString*>* head=[ends[0] componentsSeparatedByString:@","];
 if(head.count>63)return nil;
 NSArray<NSString*>* entries=[head arrayByAddingObject:ends[1]];
 NSMutableArray<NSString*>* items=[NSMutableArray new];
 for(NSString* entry in entries){
  NSString* item=lookItem(normalize(entry));
  if(!item)return nil;
  [items addObject:item];
 }
 return [items componentsJoinedByString:@"、"];
}

NSString* lookSection(NSString* section){
 if([section hasPrefix:@"<blue>"]){
  NSRange black=[section rangeOfString:@"<black>"];
  if(black.location==NSNotFound||black.location<6||![section hasSuffix:@"."])return nil;
  NSString* action=lookTerm(@"look-action\t",[section substringWithRange:NSMakeRange(6,black.location-6)]);
  NSUInteger itemsStart=NSMaxRange(black);
  if(!action||section.length<=itemsStart+1)return nil;
  NSString* items=lookItemList([section substringWithRange:NSMakeRange(itemsStart,section.length-itemsStart-1)]);
  return items?[NSString stringWithFormat:@"<blue>%@<black>%@。",action,items]:nil;
 }
 if(![section hasPrefix:@"<red>"]||![section hasSuffix:@".<black>"])return nil;
 NSString* sentence=[section substringWithRange:NSMakeRange(5,section.length-13)];
 for(NSString* verb in @[@" is wielding ",@" is holding "]){
  NSRange split=[sentence rangeOfString:verb];
  if(split.location==NSNotFound)continue;
  NSString* action=lookTerm(@"look-action\t",[sentence substringToIndex:NSMaxRange(split)-1]);
  NSString* item=lookItem([sentence substringFromIndex:NSMaxRange(split)]);
  if(action&&item)return [NSString stringWithFormat:@"<red>%@%@。<black>",action,item];
 }
 return nil;
}

NSString* composeLook(NSString* source,const char* context){
 if(!strcmp(context,"showtext")&&[source hasPrefix:@"Chatting with "]){
  NSString* identity=lookIdentity([source substringFromIndex:14]);
  return identity?[NSString stringWithFormat:@"正在与 %@ 交谈",identity]:nil;
 }
 if(!strcmp(context,"npc-talk")&&[source hasPrefix:@"It is "]&&[source hasSuffix:@" village."]&&source.length>15){
  NSString* adjective=[source substringWithRange:NSMakeRange(6,source.length-15)];
  NSString* culture=lookTerm(@"look-culture\t",adjective);
  return culture?[NSString stringWithFormat:@"那是%@的村庄。",culture]:nil;
 }
 if(drawingProfileUnit&&!strcmp(context,"showtext"))return matchTemplate(source,@"profile-unit");
 bool paragraph=!strcmp(context,"paragraph");
 bool message=!strcmp(context,"message");
 if(!paragraph&&!message&&strcmp(context,"showtext")&&strcmp(context,"renshow"))return nil;
 if((paragraph||message)&&([source hasPrefix:@"You see "]||[source hasPrefix:@"#You see "])&&[source hasSuffix:@" there."]){
  NSUInteger start=[source hasPrefix:@"#"]?9:8;
  if(source.length<=start+7)return nil;
  NSString* person=lookIdentity([source substringWithRange:NSMakeRange(start,source.length-start-7)]);
  return person?[NSString stringWithFormat:@"你看见那里有一位%@。",person]:nil;
 }
 if(message)return nil;
 if(!paragraph||![source containsString:@"<br>"])return lookIdentity(source);

 NSArray<NSString*>* sections=[source componentsSeparatedByString:@"<br>"];
 if(sections.count>32||![sections[0] hasSuffix:@"."])return nil;
 NSString* person=lookIdentity([sections[0] substringToIndex:[sections[0] length]-1]);
 if(!person)return nil;
 NSMutableString* result=[NSMutableString stringWithFormat:@"%@。",person];
 for(NSUInteger i=1;i<sections.count;i++){
  [result appendString:@"<br>"];
  NSString* section=sections[i];
  if(!section.length)continue;
  NSString* translated=lookSection(section);
  if(!translated)return nil;
  [result appendString:translated];
 }
 return result;
}

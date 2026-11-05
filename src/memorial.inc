thread_local bool drawingCultureMenu=false;

int chooseCulture(){
 auto fn=original<int(*)()>("choose_culture");
 const bool previous=drawingCultureMenu;
 drawingCultureMenu=true;
 int selected=fn();
 drawingCultureMenu=previous;
 return selected;
}

NSString* memorialWord(NSString* group,NSString* source){
 return state().dictionary[[group stringByAppendingString:source]];
}

NSString* memorialDate(NSString* source){
 static NSRegularExpression* grammar=[NSRegularExpression regularExpressionWithPattern:
  @"\\A(He|She) faced (?:his|her) end in ([a-z ]+), during ([A-Za-z ]+), on (?:day ([0-9]{1,2}) of (last|[0-9]{1,2}(?:st|nd|rd|th)) week before (midsummer point|midwinter point)|([0-9]{1,2})(?:st|nd|rd|th) of month:([0-9]{1,2}))\\.\\z"
  options:0 error:nil];
 auto match=[grammar firstMatchInString:source options:0 range:NSMakeRange(0,source.length)];
 if(!match)return nil;
 auto field=[&](NSUInteger index)->NSString*{
  NSRange range=[match rangeAtIndex:index];
  return range.location==NSNotFound?nil:[source substringWithRange:range];
 };
 NSString* season=memorialWord(@"memorial-season\t",field(2));
 NSString* phase=field(3);
 NSString* phaseEnding=@"";
 for(NSString* prefix in @[@"beginning of ",@"early ",@"late ",@"end of "]){
  if(![phase hasPrefix:prefix])continue;
  phase=[phase substringFromIndex:prefix.length];
  phaseEnding=memorialWord(@"memorial-phase\t",normalize(prefix));
  break;
 }
 NSString* month=memorialWord(@"memorial-month\t",phase);
 if(!season||!month||!phaseEnding)return nil;
 NSString* date=nil;
 if(NSString* day=field(4)){
  NSString* week=field(5);
  week=[week isEqual:@"last"]?@"最后一":[@"第 " stringByAppendingString:[week substringToIndex:week.length-2]];
  date=[NSString stringWithFormat:@"%@前%@周第 %@ 天",[field(6) hasPrefix:@"midsummer"]?@"仲夏":@"仲冬",week,day];
 }else date=[NSString stringWithFormat:@"%@ 月 %@ 日",field(8),field(7)];
 return [NSString stringWithFormat:@"%@于%@%@%@（%@）去世。",[field(1) isEqual:@"She"]?@"她":@"他",season,month,phaseEnding,date];
}

NSString* memorialCause(NSString* source){
 NSString* cause=[source lowercaseString];
 if(NSString* exact=memorialWord(@"memorial-cause\t",cause))return exact;
 for(NSString* prefix in @[@"killed by ",@"died from ",@"bled to death after "]){
  if(![cause hasPrefix:prefix]||source.length<=prefix.length)continue;
  NSString* detail=[source substringFromIndex:prefix.length];
  NSString* z=lookIdentity(detail)?:composeItem(detail);
  if(!z)return nil;
  if([prefix isEqual:@"killed by "])return [NSString stringWithFormat:@"被%@杀死",z];
  if([prefix isEqual:@"died from "])return [NSString stringWithFormat:@"因%@死亡",z];
  return [NSString stringWithFormat:@"遭遇%@后失血而死",z];
 }
 return nil;
}

NSString* memorialCauseCaption(NSString* source){
 if(![source hasSuffix:@"."])return nil;
 NSString* translated=memorialCause([source substringToIndex:source.length-1]);
 return translated?[translated stringByAppendingString:@"。"]:nil;
}

NSString* memorialPlace(NSString* source){
 NSRange end=[source rangeOfString:@" became the place of "];
 if(end.location==NSNotFound)return nil;
 NSString* tail=[source substringFromIndex:NSMaxRange(end)];
 bool female=[tail hasPrefix:@"her death. There she "];
 NSString* lead=female?@"her death. There she ":@"his death. There he ";
 if(![tail hasPrefix:lead]||![tail hasSuffix:@"."]||tail.length<=lead.length+1)return nil;

 NSString* where=[source substringToIndex:end.location];
 NSString* region=nil;
 NSRange in=[where rangeOfString:@" in " options:NSBackwardsSearch];
 if(in.location!=NSNotFound){
  region=translateMapRegion([where substringFromIndex:NSMaxRange(in)]);
  if(region)where=[where substringToIndex:in.location];
 }
 NSString* location=translateMapLocation(where)?:where;
 if(region)location=[NSString stringWithFormat:@"%@的%@",region,location];
 NSString* rawCause=[tail substringWithRange:NSMakeRange(lead.length,tail.length-lead.length-1)];
 NSString* cause=memorialCause(rawCause);
 NSString* person=female?@"她":@"他";
 if(!cause)return [NSString stringWithFormat:@"%@在%@去世。死因：%@。",person,location,rawCause];
 return [NSString stringWithFormat:@"%@在%@%@。",person,location,cause];
}

NSString* composeMemorial(NSString* source,const char* context){
 if(!strcmp(context,"paragraph")){
  if([source hasPrefix:@"He faced his end "]||[source hasPrefix:@"She faced her end "])return memorialDate(source);
  return memorialPlace(source);
 }
 if(strcmp(context,"showtext"))return nil;
 if(drawingCultureMenu)return memorialWord(@"culture-menu\t",source);
 if(drawingProfileName){
  NSRange split=[source rangeOfString:@" " options:NSBackwardsSearch];
  if(split.location!=NSNotFound){
   NSString* culture=memorialWord(@"culture-menu\t",[source substringFromIndex:NSMaxRange(split)]);
   if(culture)return [NSString stringWithFormat:@"%@ · %@",[source substringToIndex:split.location],culture];
  }
 }
 return nil;
}

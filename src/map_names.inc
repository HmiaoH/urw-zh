// get_areaname joins one reviewed English prefix and one reviewed suffix.
// Its underscores are emitted either as one space or removed at the join.
NSString* mapNameWord(NSString* group,NSString* word){
 return state().dictionary[[group stringByAppendingString:[word lowercaseString]]];
}

NSString* translateMapGloss(NSString* source){
 NSString* key=normalize(source);
 if(!key.length||key.length>48)return nil;
 if(NSString* exact=mapNameWord(@"map-gloss\t",key))return exact;
 NSString* answer=nil;
 for(NSUInteger cut=1;cut<key.length;cut++){
  NSString* head=[key substringToIndex:cut];
  NSString* tail=[key substringFromIndex:cut];
  bool spaced=[tail hasPrefix:@" "];
  if(spaced)tail=[tail substringFromIndex:1];
  NSString* spacedPrefix=spaced?mapNameWord(@"map-prefix-space\t",head):nil;
  NSString* spacedSuffix=spaced?mapNameWord(@"map-suffix-space\t",tail):nil;
  if(spaced&&!spacedPrefix&&!spacedSuffix)continue;
  NSString* prefix=spacedPrefix?:mapNameWord(@"map-prefix\t",head);
  NSString* suffix=spacedSuffix?:mapNameWord(@"map-suffix\t",tail);
  if(!prefix||!suffix)continue;
  NSString* combined=[prefix stringByAppendingString:suffix];
  if(answer&&![answer isEqual:combined])return nil;
  answer=combined;
 }
 return answer;
}

NSString* translateQuotedMapGloss(NSString* source){
 if(source.length<3||![source hasPrefix:@"\""]||![source hasSuffix:@"\""])return nil;
 NSString* gloss=translateMapGloss([source substringWithRange:NSMakeRange(1,source.length-2)]);
 return gloss?[NSString stringWithFormat:@"「%@」",gloss]:nil;
}

NSString* translateMapRegion(NSString* source){
 NSString* description=normalize(source);
 if(NSString* region=mapNameWord(@"map-region\t",description))return region;
 NSRange split=[description rangeOfString:@" "];
 if(split.location==NSNotFound)return nil;
 NSString* direction=mapNameWord(@"map-region-direction\t",[description substringToIndex:split.location]);
 NSString* region=mapNameWord(@"map-region\t",[description substringFromIndex:NSMaxRange(split)]);
 return direction&&region?[NSString stringWithFormat:@"%@ · %@",region,direction]:nil;
}

// navitxt_Dir appends a heading, optionally marked as exactly aligned.
static NSString* localHeading(NSString* source){
 if(!source)return nil;
 NSString* direction=extraBetween(source,@"in the ",@"");
 if(direction)return extraDirections()[direction];
 direction=extraBetween(source,@"directly in the ",@"");
 NSString* translated=direction?extraDirections()[direction]:nil;
 return translated?[@"正" stringByAppendingString:translated]:nil;
}

// KysySotuCreSijainti uses the corner, nearby, and direct heading cases.
static NSString* localPersonWhere(NSString* source){
 if([source isEqual:@"just around the corner"])return @"拐角附近";
 if(NSString* heading=extraBetween(source,@"just nearby ",@"")){
  NSString* direction=localHeading(heading);
  return direction?[direction stringByAppendingString:@"边不远处"]:nil;
 }
 NSString* direction=localHeading(source);
 return direction?[direction stringByAppendingString:@"边"]:nil;
}

// navitxt_LocalSpot gives a distance only for the farther water-supply case.
static NSString* localWaterWhere(NSString* source){
 static NSRegularExpression* distance=[NSRegularExpression regularExpressionWithPattern:
  @"\\Aabout ([0-9]{1,5}) (yards|meters) away (.+)\\z" options:0 error:nil];
 auto match=[distance firstMatchInString:source options:0 range:NSMakeRange(0,source.length)];
 if(match){
  NSString* heading=localHeading([source substringWithRange:[match rangeAtIndex:3]]);
  if(!heading)return nil;
  NSString* amount=[source substringWithRange:[match rangeAtIndex:1]];
  NSString* unit=[[source substringWithRange:[match rangeAtIndex:2]] isEqual:@"yards"]?@"码":@"米";
  return [NSString stringWithFormat:@"在%@边约%@%@处",heading,amount,unit];
 }
 if(NSString* visible=extraBetween(source,@"right over there ",@", you see")){
  NSString* heading=localHeading(visible);
  return heading?[NSString stringWithFormat:@"就在%@边，你看",heading]:nil;
 }
 bool indoors=[source hasPrefix:@"inside "];
 if(indoors)source=[source substringFromIndex:7];
 for(NSArray* row in @[@[@"just around the corner ",@"拐角处"],@[@"just nearby ",@"不远处"]]){
  if(NSString* rest=extraBetween(source,row[0],@"")){
   NSString* heading=localHeading(rest);
   return heading?[NSString stringWithFormat:@"就在%@边%@%@",heading,row[1],indoors?@"的屋里":@""]:nil;
  }
 }
 NSString* heading=localHeading(source);
 return heading?[NSString stringWithFormat:@"在%@边%@",heading,indoors?@"屋里":@""]:nil;
}

static NSString* composeLocalDialogue(NSString* source){
 if(NSString* water=extraBetween(source,@"Our water supply is ",@".")){
  NSString* where=localWaterWhere(water);
  return where?[NSString stringWithFormat:@"我们的取水点%@。",where]:nil;
 }
 for(NSArray* person in @[@[@"he",@"他"],@[@"she",@"她"]]){
  NSString* subject=person[0],*pronoun=person[1];
  NSString* upper=[subject capitalizedString];
  if([source isEqual:[NSString stringWithFormat:@"%@ is right over there, behind your back.",upper]])
   return [pronoun stringByAppendingString:@"就在你身后。"];
  if([source isEqual:[NSString stringWithFormat:@"%@ is right over there, you see.",upper]])
   return [pronoun stringByAppendingString:@"就在那里，你看。"];
  if([source isEqual:[NSString stringWithFormat:@"I think %@ is around here, but I don't know where exactly.",subject]])
   return [NSString stringWithFormat:@"我想%@就在附近，但不知道具体在哪儿。",pronoun];

  NSString* nearby=[NSString stringWithFormat:@"At least a moment ago %@ was wandering around here ",subject];
  if(NSString* location=extraBetween(source,nearby,@".")){
   NSString* where=localPersonWhere(location);
   return where?[NSString stringWithFormat:@"至少刚才，%@还在%@转悠。",pronoun,where]:nil;
  }
  NSString* indoors=[NSString stringWithFormat:@"A while ago %@ was inside ",subject];
  if(NSString* location=extraBetween(source,indoors,@".")){
   NSString* where=localPersonWhere(location);
   return where?[NSString stringWithFormat:@"刚才%@还在%@的屋子里。",pronoun,where]:nil;
  }
 }
 return nil;
}

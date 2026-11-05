// Expanded map Note forms. All variable fields use bounded native vocabularies.
NSString* translateTerrainName(NSString* source);

NSString* notificationTracks(NSString* source){
 NSString* body=notificationSpan(source,@"Here you notice ",@".");
 if(!body||body.length>180)return nil;
 static NSDictionary* ages=@{
  @"very fresh":@"刚留下的",@"fresh":@"新鲜的",@"quite fresh":@"还算新鲜的",
  @"an hour old":@"约一小时前的",@"some hours old":@"几小时前的",
  @"half a day old":@"半天前的",@"day old":@"一天前的",
  @"few days old":@"几天前的",@"old":@"陈旧的"
 };
 NSString* age=nil;
 for(NSString* label in ages){
  NSString* prefix=[label stringByAppendingString:@" "];
  if([body hasPrefix:prefix]){
   age=ages[label];
   body=[body substringFromIndex:prefix.length];
   break;
  }
 }
 if(!age)return nil;
 NSRange split=[body rangeOfString:@" tracks "];
 if(split.location==NSNotFound||!split.location)return nil;
 NSString* species=[body substringToIndex:split.location];
 NSString* tail=[body substringFromIndex:NSMaxRange(split)];
 NSString* gait=@"";
 for(NSArray<NSString*>* variant in @[@[@"running",@"奔跑时留下的"],@[@"limping",@"跛行时留下的"]]){
  NSString* suffix=[@" " stringByAppendingString:variant[0]];
  if([species hasSuffix:suffix]){
   gait=variant[1];
   species=[species substringToIndex:species.length-suffix.length];
   break;
  }
 }
 static NSDictionary* speciesNames=@{
  @"human":@"人类",@"unknown":@"不明生物",@"elk":@"驼鹿",@"forest reindeer":@"森林驯鹿",
  @"wolf":@"狼",@"lynx":@"猞猁",@"bear":@"熊",@"brown bear":@"棕熊",@"fox":@"狐狸",
  @"hare":@"野兔",@"beaver":@"河狸",@"wolverine":@"狼獾",@"otter":@"水獭"
 };
 NSString* name=speciesNames[species]?:animalDescription(species);
 if(!name)return nil;
 NSString* path=nil;
 if([tail hasPrefix:@"leading "]){
  if(NSString* direction=extraDirections()[[tail substringFromIndex:8]])path=[@"通向" stringByAppendingString:direction];
 }else if([tail isEqual:@"which are numerous and mixed"])path=@"足迹很多，彼此交错";
 else if([tail isEqual:@"mixed with some other unclear tracks"])path=@"混有其他模糊的足迹";
 return path?[NSString stringWithFormat:@"你在这里发现了%@%@%@足迹，%@。",age,name,gait,path]:nil;
}

NSString* composeMapNotification(NSString* source){
 if(NSString* tracks=notificationTracks(source))return tracks;
 static NSArray* forms=@[
  @[@" here and you take a closer look at this area.",@"你仔细察看了这片%@。"],
  @[@" here and you encounter something.",@"你在这片%@遇到了什么。"]
 ];
 for(NSArray<NSString*>* form in forms){
  NSString* raw=notificationSpan(source,@"There is ",form[0]);
  if(!raw||raw.length>80)continue;
  NSString* capitalized=[[[raw substringToIndex:1] uppercaseString] stringByAppendingString:[raw substringFromIndex:1]];
  NSString* terrain=translateTerrainName(raw)?:translateTerrainName(capitalized);
  if(terrain)return [NSString stringWithFormat:form[1],terrain];
 }
 return nil;
}

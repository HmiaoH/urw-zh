// Complete Note strings only. Never translate individual native word fragments.
NSString* messageItem(NSString* s){
 for(NSString* article in @[@"a ",@"an ",@"the ",@"The "])if([s hasPrefix:article]){s=[s substringFromIndex:article.length];break;}
 return composeItem(s);
}
NSString* composeMessage(NSString* s){
 if([s hasPrefix:@"#You see "]){
  for(NSString* end in @[@" here.",@" there."])if([s hasSuffix:end]){
   NSString* item=messageItem([s substringWithRange:NSMakeRange(9,s.length-9-end.length)]);
   return item?[NSString stringWithFormat:@"你看到%@有%@。",[end isEqual:@" here."]?@"这里":@"那里",item]:nil;
  }
 }
 if([s hasPrefix:@"+The "]){
  for(NSString* role in @[@"primary",@"secondary"]){
   NSString* end=[NSString stringWithFormat:@" wielded as a %@ weapon.",role];
   if([s hasSuffix:end]){NSString* item=composeItem([s substringWithRange:NSMakeRange(5,s.length-5-end.length)]);return item?[NSString stringWithFormat:@"已将%@用作%@武器。",item,[role isEqual:@"primary"]?@"主要":@"副手"]:nil;}
  }
 }
 if([s isEqual:@"!You can't walk through the fire!"])return @"你不能穿过火堆！";
 if([s isEqual:@"!That's too steep to be climbed!"])return @"那里太陡，爬不上去！";
 NSString* start=@"!There's ",*end=@" blocking your way!";
 if([s hasPrefix:start]&&[s hasSuffix:end]){
  NSString* object=[s substringWithRange:NSMakeRange(start.length,s.length-start.length-end.length)];
  NSDictionary* trees=@{@"a spruce":@"一棵云杉",@"a young spruce":@"一棵云杉幼树",@"a pine":@"一棵松树",@"a young pine":@"一棵松树幼树",@"a birch":@"一棵桦树",@"a young birch":@"一棵桦树幼树"};
  NSString* name=trees[object]?:messageItem(object);
  NSDictionary* sides=@{@"northern":@"北侧",@"southern":@"南侧",@"eastern":@"东侧",@"western":@"西侧",@"north-east":@"东北",@"north-west":@"西北",@"south-east":@"东南",@"south-west":@"西南"};
  for(NSString* side in sides)for(NSString* part in @[@"wall",@"corner"])if([object isEqual:[NSString stringWithFormat:@"a %@ %@ of a kota",side,part]])name=[NSString stringWithFormat:@"科塔帐篷的%@%@",sides[side],[part isEqual:@"wall"]?@"帐壁":@"角"];
  return name?[name stringByAppendingString:@"挡住了你的路！"]:nil;
 }
 return nil;
}

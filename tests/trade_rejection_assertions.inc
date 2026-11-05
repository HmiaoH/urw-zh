 NSArray* rejectionRules=zh::json(@"data/rules/trade_rejections.json")[@"templates"];
 assert(rejectionRules.count==16);
 for(NSDictionary* r in rejectionRules){
  NSString* source=[r[@"original"] stringByReplacingOccurrencesOfString:@"%s" withString:@"fine hunting knife"];
  auto translated=zh::translate(source.UTF8String,"npc-talk");assert(translated);assert([translated containsString:@"精良猎刀"]);
  assert(!zh::composeTradeRejection([r[@"original"] stringByReplacingOccurrencesOfString:@"%s" withString:@"unrecognized relic"]));
  assert(!zh::translate(source.UTF8String,"showtext"));
 }
 assert([zh::composeTradeRejection(@"No, we don't need more fish products. We have decent reserves already.") containsString:@"鱼制品"]);

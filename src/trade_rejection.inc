// Display-only tradeacc rejection grammar. All native reason families; unknown items fail closed.
NSString* composeTradeRejection(NSString* source){
 if(source.length>1023)return nil;
 if([source isEqual:@"We want furs - tanned furs. Thick and fine furs of the north. You understand?"])return @"我们要毛皮——鞣制好的毛皮，北方厚实的上等毛皮。明白了吗？";
 static NSArray* rules=@[
  @[@"It's you who wants ",@", not me.",@"想要%@的是你，不是我。"],
  @[@"What!? You consider ",@" valuable? Well, I do not.",@"什么？你觉得%@值钱？我可不这么想。"],
  @[@"",@"? No thank you.",@"%@？不用了，谢谢。"],
  @[@"I'm afraid that ",@" is too much for me to carry right now.",@"恐怕我现在拿不动%@。"],
  @[@"",@"? Those aren't needed.",@"%@？我们不需要这些。"],
  @[@"I wouldn't want to reject those ",@", but I'm too burdened to carry them.",@"我也想收下那些%@，可我已经拿不动更多东西了。"],
  @[@"You try to trade with ",@"? No thanks.",@"你想拿%@来换？不用了。"],
  @[@"We don't need that many ",@".",@"我们不需要那么多%@。"],
  @[@"No thanks, we have enough ",@" already.",@"不用了，我们的%@已经够多了。"],
  @[@"No, we don't need more ",@". We have decent reserves already.",@"不用，我们不缺%@，储备已经够了。"],
  @[@"That ",@" is not yours.",@"那%@不是你的。"],
  @[@"I don't need any more ",@".",@"我不需要更多%@。"],
  @[@"That ",@" is not of quality I expect.",@"那%@的品质达不到我的要求。"],
  @[@"I certainly don't want your unknown ",@".",@"我可不想要你那些来历不明的%@。"],
  @[@"That ",@" is unworthy in this barter.",@"那%@在这笔交易里抵不了什么。"],
  @[@"Have that ",@" tanned first then let's see about it.",@"先把那%@鞣制好，我们再谈。"],
];
 for(NSArray* rule in rules){
  NSString* item=extraBetween(source,rule[0],rule[1]);if(!item)continue;
  NSString* key=[item lowercaseString];
  static NSDictionary* categories=@{@"that":@"这些东西",@"meat":@"肉",@"fish":@"鱼",@"meat products":@"肉制品",@"fish products":@"鱼制品"};
  NSString* name=categories[key]?:composeItem(item);
  return name?[NSString stringWithFormat:rule[2],name]:nil;
 }
 return nil;
}

 // Native ages, compass headings and gait/size combinations remain bounded.
 {
  NSArray* ages=@[@"very fresh",@"fresh",@"quite fresh",@"an hour old",@"some hours old",@"half a day old",@"day old",@"few days old",@"old"];
  for(NSString* age in ages)for(NSString* direction in zh::extraDirections()){
   NSString* source=[NSString stringWithFormat:@"Here you notice %@ wolf tracks leading %@.",age,direction];
   assert(zh::translate(source.UTF8String,"message"));
  }
  assert([zh::translate("Here you notice fresh big forest reindeer limping tracks leading south-west.","message") isEqual:@"你在这里发现了新鲜的大森林驯鹿跛行时留下的足迹，通向西南。"]);
  assert([zh::translate("Here you notice old small human running tracks which are numerous and mixed.","message") isEqual:@"你在这里发现了陈旧的小人类奔跑时留下的足迹，足迹很多，彼此交错。"]);
  assert([zh::translate("Here you notice day old unknown tracks mixed with some other unclear tracks.","message") isEqual:@"你在这里发现了一天前的不明生物足迹，混有其他模糊的足迹。"]);
  for(NSString* creature in @[@"arctic fox",@"wild boar",@"wild sow",@"badger",@"squirrel",@"pine-marten",@"polecat",@"ermine",@"weasel",@"grey seal",@"ringed seal",@"glutton",@"black grouse",@"hazel grouse",@"raven",@"willow grouse",@"capercaillie",@"aquatic bird",@"swan",@"goldeneye",@"kuikka",@"tufted duck",@"eagle owl",@"dog",@"reindeer calf"]){
   NSString* source=[NSString stringWithFormat:@"Here you notice fresh big %@ running tracks leading north.",creature];
   assert(zh::translate(source.UTF8String,"message"));
  }
  for(NSString* source in @[@"Here you notice ancient wolf tracks leading north.",@"Here you notice fresh huge wolf tracks leading north.",@"Here you notice fresh wolf crawling tracks leading north.",@"Here you notice fresh dragon tracks leading north.",@"Here you notice fresh wolf tracks leading upwards.",@"Here you notice fresh wolf tracks leading north. extra"])
   assert(zh::translate(source.UTF8String,"message")==nil);
  for(NSString* source in @[@"You don't notice any tracks around here.",@"=You find some tracks here.",@"=You spot some tracks close by.",@"You peer into the water. Your reflection peers back at you.",@"You think you see something moving in the depths but then it's gone.",@"You walk around a little looking for tracks...",@"There are some tracks over there.",@":As roaming ahead something suddenly captures your attention.",@"+You have improved in tracking!"])
   assert(zh::translate(source.UTF8String,"message"));
 }

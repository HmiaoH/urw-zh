// These rules match complete expanded Note messages. Captures for plant,
// identity and item slots each pass through their own reviewed vocabulary.
NSString* notificationSpan(NSString* source,NSString* start,NSString* end){
 if(source.length<=start.length+end.length||(start.length&&![source hasPrefix:start])||(end.length&&![source hasSuffix:end]))return nil;
 return [source substringWithRange:NSMakeRange(start.length,source.length-start.length-end.length)];
}

NSString* notificationPlantName(NSString* source){
 if([source hasPrefix:@"the "]||[source hasPrefix:@"The "])source=[source substringFromIndex:4];
 NSString* plant=[source lowercaseString];
 auto& s=state();
 NSString* prefix=@"notification-plant\t";
 NSString* direct=s.dictionary[[prefix stringByAppendingString:plant]];
 if(direct)return direct;
 NSString* singular=s.itemRules[@"plurals"][plant];
 return singular?s.dictionary[[prefix stringByAppendingString:singular]]:nil;
}

NSString* notificationPlant(NSString* source){
 bool patch=[source hasPrefix:@"a patch of "];
 if(patch)source=[source substringFromIndex:11];
 bool single=[source hasPrefix:@"a "]||[source hasPrefix:@"an "];
 NSString* count=nil;
 if(single){
  if(patch)return nil;
  source=[source substringFromIndex:[source hasPrefix:@"an "]?3:2];
  if([source hasSuffix:@" patch"]){
   patch=true;
   source=[source substringToIndex:source.length-6];
  }
 }else{
  NSRange space=[source rangeOfString:@" "];
  if(space.location==NSNotFound)return nil;
  count=[source substringToIndex:space.location];
  if([count rangeOfString:@"\\A(?:[2-9]|[1-9][0-9]{1,3})\\z" options:NSRegularExpressionSearch].location==NSNotFound)return nil;
  source=[source substringFromIndex:NSMaxRange(space)];
 }
 NSRange split=[source rangeOfString:@" "];
 if(split.location==NSNotFound)return nil;
 NSString* stage=[source substringToIndex:split.location];
 static NSDictionary* stages=@{@"growing":@"生长中的",@"withering":@"正在枯萎的",@"picked":@"已采摘的"};
 NSString* stateName=stages[stage];
 if(!stateName)return nil;
 NSString* name=notificationPlantName([source substringFromIndex:NSMaxRange(split)]);
 if(!name)return nil;
 if(patch)return count?[NSString stringWithFormat:@"一片%@%@（%@ 株）",stateName,name,count]:[NSString stringWithFormat:@"一片%@%@",stateName,name];
 return count?[NSString stringWithFormat:@"%@ 株%@%@",count,stateName,name]:[NSString stringWithFormat:@"一株%@%@",stateName,name];
}

NSString* notificationSkill(NSString* skill){
 static NSSet<NSString*>* names=[NSSet setWithArray:@[
  @"DODGE",@"UNARMED",@"KNIFE",@"SWORD",@"AXE",@"SPEAR",@"CLUB",@"BOW",@"CROSSBOW",@"SHIELD",
  @"AGRICULTURE",@"HERBLORE",@"FISHING",@"NETMAKING",@"TRACKING",@"TRAPPING",@"HIDEWORKING",
  @"TIMBERCRAFT",@"BUILDING",@"CARPENTRY",@"COOKERY",@"PHYSICIAN",@"WEATHERLORE",@"TEXTILECRAFT",
  @"CLOTHCRAFT",@"BOWYER",@"CLIMBING",@"SKIING",@"SWIMMING",@"STEALTH"
 ]];
 return [names containsObject:skill]?state().dictionary[[@"showtext\t" stringByAppendingString:skill]]:nil;
}

NSString* notificationWeapon(NSString* source){
 if(NSString* body=notificationSpan(source,@"+The applicable weapon skill for ",@"\".")){
  NSArray<NSString*>* parts=[body componentsSeparatedByString:@" is \""];
  if(parts.count!=2)return nil;
  NSString* item=messageItem(parts[0]),*skill=notificationSkill(parts[1]);
  return item&&skill?[NSString stringWithFormat:@"%@适用的武器技能是%@。",item,skill]:nil;
 }
 NSString* body=notificationSpan(source,@"+Weapon classification of ",@" bonus to defense.");
 if(!body)return nil;
 NSArray<NSString*>* parts=[body componentsSeparatedByString:@" gives it "];
 if(parts.count!=2)return nil;
 NSArray<NSString*>* bonus=[parts[1] componentsSeparatedByString:@" bonus to attack, and "];
 if(bonus.count!=2)return nil;
 static NSDictionary* levels=@{@"zero":@"无",@"a very little":@"极小",@"a little":@"少量",
  @"a decent":@"适中",@"a good":@"较高",@"a remarkable":@"显著",@"a superior":@"极高"};
 NSString* item=messageItem(parts[0]),*attack=levels[bonus[0]],*defense=levels[bonus[1]];
 return item&&attack&&defense?[NSString stringWithFormat:@"%@的攻击加成：%@，防御加成：%@。",item,attack,defense]:nil;
}

NSString* composeNotificationFollowup(NSString* source){
 if(NSString* usingSkill=notificationSpan(source,@"#Using: ",@"")){
  if(NSString* skill=notificationSkill(usingSkill))return [@"正在使用：" stringByAppendingString:skill];
 }
 if([source hasPrefix:@"+"]){
  if(NSString* weapon=notificationWeapon(source))return weapon;
 }
 if([source hasPrefix:@"#You see "]){
  for(NSString* place in @[@"here",@"there"]){
   NSString* end=[NSString stringWithFormat:@" %@.",place];
   NSString* subject=notificationSpan(source,@"#You see ",end);
   if(!subject)continue;
   NSString* where=[place isEqual:@"here"]?@"这里":@"那里";
   if(NSString* plant=notificationPlant(subject))
    return [NSString stringWithFormat:@"你看到%@有%@。",where,plant];
   if([subject hasPrefix:@"the "]||[subject hasPrefix:@"The "])subject=[subject substringFromIndex:4];
   if(NSString* person=lookIdentity(subject))
    return [NSString stringWithFormat:@"你看到%@有一位%@。",where,person];
   if(NSString* thing=state().dictionary[[@"notification-observation\t" stringByAppendingString:subject]])
    return [NSString stringWithFormat:@"你看到%@有%@。",where,thing];
  }
 }
 if(NSString* subject=notificationSpan(source,@"",@" withdraws from your way.")){
  if([subject hasPrefix:@"the "]||[subject hasPrefix:@"The "])subject=[subject substringFromIndex:4];
  if(NSString* person=lookIdentity(subject))
   return [person stringByAppendingString:@"给你让开了路。"];
 }

 static NSArray* durationRules=@[
  @[@":It will be fully ripe after ",@"%@后完全成熟。"],
  @[@":It will be flowering after ",@"%@后开花。"],
  @[@":It's withering and will die in ",@"正在枯萎，%@后会枯死。"]
 ];
 for(NSArray<NSString*>* rule in durationRules){
  NSString* duration=notificationSpan(source,rule[0],@".");
  if(!duration)continue;
  NSString* translated=state().dictionary[[@"notification-duration\t" stringByAppendingString:duration]];
  if(translated)return [NSString stringWithFormat:rule[1],translated];
 }
 static NSArray* harvestRules=@[
  @[@"#Gathering ",@"...",@"正在采集%@……"],
  @[@"!The ",@" here isn't ripe for harvesting yet.",@"这里的%@还没成熟，暂时不能采收。"],
  @[@"!The ",@" here isn't ripe yet, but there are young leaves already.",@"这里的%@还没成熟，但已经长出了嫩叶。"],
  @[@"!The ",@" here isn't ripe yet, but can be harvested for fibre already.",@"这里的%@还没成熟，但已能收割纤维。"],
  @[@"!The ",@" here has been picked already!",@"这里的%@已经采过了！"],
  @[@"!The ",@" here is past its flowering period and will not yield flowers.",@"这里的%@已过花期，采不到花了。"],
  @[@"!This ",@" no longer provides any yield nor carries any usable parts.",@"这株%@已没有可采收的部分。"],
  @[@"!This ",@" doesn't carry usable parts to pick, try to harvest and thresh it.",@"这株%@已无可摘取的部分，可以试着收割并脱粒。"],
  @[@"!This early-harvested ",@" doesn't provide any yield.",@"这株%@收割过早，没有收成。"]
 ];
 for(NSArray<NSString*>* rule in harvestRules){
  NSString* subject=notificationSpan(source,rule[0],rule[1]);
  if(!subject)continue;
  if(NSString* plant=notificationPlantName(subject))return [NSString stringWithFormat:rule[2],plant];
 }
 static NSArray* itemRules=@[
  @[@":You pick up the ",@".",@"你捡起了%@。"],
  @[@":You drop the ",@".",@"你放下了%@。"],
  @[@"+You take off your ",@".",@"你取下了%@。"],
  @[@"+You empty ",@" to have it filled again.",@"你倒空了%@，可以重新装填。"],
  @[@":You got ",@".",@"你采到了%@。"],
  @[@":You finish eating some of that ",@".",@"你吃了一些%@。"],
  @[@":You finish eating ",@".",@"你吃完了%@。"],
  @[@"It's plain good ",@".",@"%@味道不错。"],
  @[@"Ok. You harvested down ",@".",@"你收割了%@。"]
 ];
 for(NSArray<NSString*>* rule in itemRules){
  NSString* subject=notificationSpan(source,rule[0],rule[1]);
  if(!subject)continue;
  NSString* item=messageItem(subject)?:lookItemList(subject);
  if(item)return [NSString stringWithFormat:rule[2],item];
 }
 return nil;
}

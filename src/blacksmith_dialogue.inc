// Original BlacksmithDataList products. Keep the parser's product and order IDs untouched.
static NSDictionary* blacksmithProducts() {
 static NSDictionary* products = @{
  @"knife":@"刀", @"small knife":@"小刀", @"broad knife":@"宽刃刀", @"hunting knife":@"猎刀",
  @"fisher's knife":@"渔刀", @"kaumolais knife":@"考莫刀", @"northern knife":@"北方刀", @"skramasaksi":@"斯克拉马短刀",
  @"sickle":@"镰刀", @"pot":@"锅", @"shovel":@"铲", @"iron fishhook":@"铁鱼钩", @"iron sewing needle":@"铁缝衣针",
  @"handaxe":@"手斧", @"carving axe":@"雕刻斧", @"splitting axe":@"劈柴斧", @"woodsman's axe":@"伐木斧", @"broad axe":@"宽刃斧",
  @"spear":@"矛", @"kaumolais spear":@"考莫矛", @"northern spear":@"北方矛", @"ango":@"安戈矛",
  @"trident":@"三叉戟", @"wide trident":@"宽头三叉戟", @"arrowhead":@"箭镞", @"broadhead":@"宽头箭镞",
  @"shortsword":@"短剑", @"broadsword":@"阔剑", @"iron helm":@"铁头盔", @"iron spectacle helm":@"铁护目盔",
  @"roundshield":@"圆盾",
 };
 return products;
}

static NSString* blacksmithBatch(NSString* name) {
 static NSDictionary* plurals = @{
  @"iron fishhooks":@"铁鱼钩", @"arrowheads":@"箭镞", @"broadheads":@"宽头箭镞",
 };
 return plurals[name];
}

static NSString* blacksmithWithoutArticle(NSString* source) {
 if ([source hasPrefix:@"an "]) return [source substringFromIndex:3];
 if ([source hasPrefix:@"a "]) return [source substringFromIndex:2];
 return source;
}

static NSString* blacksmithDuration(NSString* source) {
 // TIMESPAN_DAY resource expansions.
 static NSDictionary* spans = @{
  @"a day":@"一天", @"two days":@"两天", @"few days":@"几天", @"half a week":@"半周",
  @"a week":@"一周", @"two weeks":@"两周", @"couple of weeks":@"两周左右", @"a month":@"一个月",
  @"over a month":@"一个多月", @"nearly two months":@"将近两个月", @"few months":@"几个月",
  @"couple of months":@"两个月左右", @"several months":@"数月", @"many months":@"许多个月",
  @"half a year":@"半年", @"a year":@"一年", @"over a year":@"一年多", @"nearly two years":@"将近两年",
  @"few years":@"几年", @"unknown time":@"一段时间",
 };
 return spans[source];
}

static NSString* blacksmithWhen(NSString* source) {
 static NSDictionary* fixed = @{
  @"someday":@"过些日子", @"shortly":@"不久后", @"tomorrow":@"明天", @"after a while":@"过一会儿",
  @"in half an hour":@"半小时后", @"in an hour":@"一小时后", @"in a few hours":@"几小时后",
  @"by small hours":@"后半夜前", @"by early morning":@"清晨前", @"by morning":@"早晨前",
  @"by late morning":@"上午晚些时候", @"by noon":@"中午前", @"by early afternoon":@"午后不久",
  @"by afternoon":@"下午前", @"by late afternoon":@"傍晚前", @"by early evening":@"入夜前",
  @"by evening":@"晚上前", @"by late evening":@"深夜前", @"by late night":@"深夜前",
  @"by midnight":@"午夜前", @"by after midnight":@"午夜过后", @"by night":@"夜里",
 };
 if (NSString* result = fixed[source]) return result;
 NSString* after = extraBetween(source, @"after ", @"");
 if (!after) return nil;
 if (NSString* duration = blacksmithDuration(after)) return [duration stringByAppendingString:@"后"];
 NSString* days = extraBetween(after, @"", @" days");
 if (!days || [days rangeOfString:@"\\A[1-9][0-9]{0,8}\\z" options:NSRegularExpressionSearch].location == NSNotFound) return nil;
 return [days stringByAppendingString:@" 天后"];
}

static NSString* blacksmithQuoteItem(NSString* body, bool batch=false) {
 static NSDictionary* grades = @{
  @"crude":@"粗陋", @"rough":@"粗制", @"decent":@"普通", @"fine":@"精良", @"masterwork":@"大师级",
  @"leaky":@"漏水", @"beautiful":@"精美", @"ragged":@"破烂", @"harsh":@"粗硬", @"superior":@"上等",
  @"poor":@"低劣", @"inferior":@"劣质", @"perfect":@"完美",
 };
 NSString* count = @"";
 NSRange amount = [body rangeOfString:@"\\A(?:6|12) " options:NSRegularExpressionSearch];
 if (amount.location != NSNotFound) {
  count = [body substringToIndex:amount.length - 1];
  body = [body substringFromIndex:amount.length];
 } else {
  body = blacksmithWithoutArticle(body);
 }
 NSString* grade = @"";
 NSRange space = [body rangeOfString:@" "];
 if (space.location != NSNotFound) {
  if (NSString* translated = grades[[body substringToIndex:space.location]]) {
   grade = translated;
   body = [body substringFromIndex:NSMaxRange(space)];
  }
 }
 if (count.length && ![count isEqual:[body isEqual:@"iron fishhooks"] ? @"6" : @"12"]) return nil;
 NSString* name = batch || count.length ? blacksmithBatch(body) : blacksmithProducts()[body];
 if (!name) return nil;
 if (count.length) return [NSString stringWithFormat:@"%@ 个%@%@", count, grade, name];
 return [grade stringByAppendingString:name];
}

static NSString* composeBlacksmithPlayer(NSString* source) {
 if (NSString* item = extraBetween(source, @"\"I'd like to have ", @", please.\"")) {
  NSString* name = blacksmithWithoutArticle(item);
  NSString* translated = [name isEqual:item] ? nil : blacksmithProducts()[name];
  return translated ? [NSString stringWithFormat:@"“请帮我做一件%@。”", translated] : nil;
 }
 if (NSString* item = extraBetween(source, @"\"I'd like some ", @", please.\"")) {
  NSString* translated = blacksmithBatch(item);
  return translated ? [NSString stringWithFormat:@"“请帮我做一些%@。”", translated] : nil;
 }
 if (NSString* item = extraBetween(source, @"\"How's that ", @" coming along?\"")) {
  NSString* translated = blacksmithQuoteItem(item);
  return translated ? [NSString stringWithFormat:@"“我订的%@做得怎么样了？”", translated] : nil;
 }
 if (NSString* item = extraBetween(source, @"\"How are those ", @" coming along?\"")) {
  NSString* translated = blacksmithQuoteItem(item, true);
  return translated ? [NSString stringWithFormat:@"“我订的那批%@做得怎么样了？”", translated] : nil;
 }
 return nil;
}

static NSString* blacksmithProductList(NSString* source) {
 static NSDictionary* categories = @{
  @"tools":@"工具", @"knives":@"刀具", @"axes":@"斧头", @"spears":@"矛",
  @"arrowheads":@"箭镞", @"swords":@"剑", @"a helmet":@"头盔", @"a shield":@"盾牌",
 };
 NSArray* tail = [source componentsSeparatedByString:@" and "];
 if (tail.count > 2 || [tail.lastObject containsString:@", "]) return nil;
 NSArray* parts = [[tail componentsJoinedByString:@", "] componentsSeparatedByString:@", "];
 if (parts.count > 8) return nil;
 NSMutableArray* names = [NSMutableArray new];
 for (NSString* part in parts) {
  NSString* translated = categories[part] ?: blacksmithBatch(part) ?: blacksmithProducts()[blacksmithWithoutArticle(part)];
  if (!translated) return nil;
  [names addObject:translated];
 }
 return [names componentsJoinedByString:@"、"];
}

static NSString* blacksmithReward(NSString* source) {
 static NSDictionary* portions = @{
  @"almost all":@"几乎全部", @"close to all":@"接近全部", @"more than two thirds":@"三分之二以上",
  @"two thirds":@"三分之二", @"more than half":@"一半以上", @"about a half":@"大约一半",
  @"less than half":@"不到一半", @"one third":@"三分之一", @"one fifth":@"五分之一",
  @"about one tenth":@"约十分之一", @"just a little":@"一小部分", @"very, very little":@"很少一部分",
 };
 if (NSString* ratio = extraBetween(source, @"Your reward covers ", @" of this. The rest of it you have to pay.")) {
  NSString* portion = portions[ratio];
  return portion ? [NSString stringWithFormat:@"你的报酬能抵掉这笔货款的%@，剩下的还得另付。", portion] : nil;
 }
 if (NSString* ratio = extraBetween(source, @"It's all yours to keep, and makes up for ", @" of your remaining reward.")) {
  NSString* portion = portions[ratio];
  return portion ? [NSString stringWithFormat:@"这些都归你，算作你剩余报酬的%@。", portion] : nil;
 }
 return nil;
}

static NSString* composeBlacksmithNpc(NSString* source) {
 if (NSString* list = extraBetween(source, @"I can make you ", @".")) {
  NSString* names = blacksmithProductList(list);
  return names ? [NSString stringWithFormat:@"我能给你做%@。", names] : nil;
 }
 if (NSString* body = extraBetween(source, @"Very well. You shall have ", @".")) {
  NSString* item = blacksmithQuoteItem(body);
  return item ? [NSString stringWithFormat:@"好，我会给你做%@。", item] : nil;
 }
 for (NSString* suffix in @[@" to make it.", @" to make them."]) {
  if (NSString* span = extraBetween(source, @"It will take me ", suffix)) {
   NSString* when = blacksmithDuration(span);
   return when ? [NSString stringWithFormat:@"我需要%@才能做好。", when] : nil;
  }
 }
 for (NSString* prefix in @[@"I'll get started with your ", @"I'll get started with those "]) {
  NSString* body = extraBetween(source, prefix, @".");
  if (!body) continue;
  bool batch = [prefix hasSuffix:@"those "];
  NSArray* parts = [body componentsSeparatedByString:batch ? @", and expect to see you come claim them after "
                                                           : @", and expect to see you come claim it after "];
  if (parts.count != 2) return nil;
  NSString* item = batch ? blacksmithBatch(parts[0]) : blacksmithProducts()[parts[0]];
  NSString* when = blacksmithDuration(parts[1]);
  return item && when ? [NSString stringWithFormat:@"我这就开始做%@。%@后记得回来取。", item, when] : nil;
 }
 if (NSString* span = extraBetween(source, @"I'm working on it. Come ask again ", @".")) {
  NSString* when = blacksmithWhen(span);
  return when ? [NSString stringWithFormat:@"我正在做，%@再来问吧。", when] : nil;
 }
 if (NSString* span = extraBetween(source, @"It will be ready ", @".")) {
  NSString* when = blacksmithWhen(span);
  return when ? [NSString stringWithFormat:@"%@就能做好。", when] : nil;
 }
 return blacksmithReward(source);
}

// npc_trade_suggestion emits a bare andlist followed by a period in its own
// CrTalk call. Only the caller-checked NPC display path invokes this helper.
static NSString* composeTradePayment(NSString* source, NSString* (*translateItem)(NSString*)) {
 if (source.length > 1023) return nil;
 NSString* list = extraBetween(source, @"", @".");
 if (!list) return nil;
 NSArray* tail = [list componentsSeparatedByString:@" and "];
 if (tail.count > 2 || [tail.lastObject containsString:@", "]) return nil;
 NSArray* items = [[tail componentsJoinedByString:@", "] componentsSeparatedByString:@", "];
 if (items.count > 10) return nil;
 NSMutableArray* translated = [NSMutableArray new];
 for (NSString* item in items) {
  NSString* worn = extraBetween(item, @"", @" (being worn)");
  NSString* name = translateItem(worn ?: item);
  if (!name) return nil;
  [translated addObject:worn ? [name stringByAppendingString:@"（正穿戴）"] : name];
 }
 return [[translated componentsJoinedByString:@"、"] stringByAppendingString:@"。"];
}

// Native NPC replies. Match only whole utterances, with finite vocabularies
// for every generated field except names.
static NSString* extraBetween(NSString* source, NSString* prefix, NSString* suffix) {
 if ((prefix.length && ![source hasPrefix:prefix]) ||
     (suffix.length && ![source hasSuffix:suffix]) ||
     source.length <= prefix.length + suffix.length) return nil;
 return [source substringWithRange:NSMakeRange(prefix.length, source.length - prefix.length - suffix.length)];
}

static NSString* extraDistance(NSString* source) {
 static NSDictionary* fixed = @{
  @"less than a kilometer":@"不到一公里", @"half a kilometer":@"半公里",
  @"just a couple of kilometers":@"只有几公里",
  @"less than a mile":@"不到一英里", @"half a mile":@"半英里",
  @"just a couple of miles":@"只有几英里",
 };
 NSString* distance = extraBetween(source, @"", @" away");
 if (!distance) return nil;
 if (NSString* result = fixed[distance]) return result;

 static NSRegularExpression* units = [NSRegularExpression
  regularExpressionWithPattern:@"\\Aabout ([0-9]{1,10}) (kilometers|miles)\\z" options:0 error:nil];
 auto match = [units firstMatchInString:distance options:0 range:NSMakeRange(0,distance.length)];
 if (!match) return nil;
 NSString* amount = [distance substringWithRange:[match rangeAtIndex:1]];
 NSString* unit = [[distance substringWithRange:[match rangeAtIndex:2]] isEqual:@"miles"] ? @"英里" : @"公里";
 return [NSString stringWithFormat:@"约%@%@", amount, unit];
}

static NSDictionary* extraDirections() {
 static NSDictionary* directions = @{
  @"east":@"东", @"north-east":@"东北", @"north":@"北", @"north-west":@"西北",
  @"west":@"西", @"south-west":@"西南", @"south":@"南", @"south-east":@"东南",
 };
 return directions;
}

static NSString* extraRoute(NSString* source) {
 auto parts = [source componentsSeparatedByString:@", "];
 if (parts.count != 2) return nil;
 NSString* heading = extraBetween(parts[0], @"in the ", @" from here");
 bool straight = false;
 if (!heading) {
  heading = extraBetween(parts[0], @"directly in the ", @" from here");
  straight = true;
 }
 NSString* direction = heading ? extraDirections()[heading] : nil;
 NSString* distance = extraDistance(parts[1]);
 return direction && distance ? [NSString stringWithFormat:@"从这里%@向%@，%@", straight ? @"径直" : @"", direction, distance] : nil;
}

static NSString* extraWorldLocation(NSString* source) {
 NSString* location = extraBetween(source, @"It's ", @".");
 if (!location) return nil;
 NSRange marker = [location rangeOfString:@" at the region called "];
 if (marker.location == NSNotFound) marker = [location rangeOfString:@" here at "];
 NSString* region = marker.location == NSNotFound ? nil : [location substringFromIndex:NSMaxRange(marker)];
 if (marker.location != NSNotFound && !region.length) return nil;
 NSString* area = region ? [location substringToIndex:marker.location] : location;

 static NSDictionary* cultures = @{
  @"Kaumo":@"Kaumo", @"Driik":@"Driik", @"Kiesse":@"Kiesse", @"Reemi":@"Reemi",
  @"Sartola":@"Sartola", @"archipelago":@"群岛", @"Koivula":@"Koivula",
  @"Kuikka-tribe lands":@"库伊卡部族领地", @"Owl-tribe lands":@"鸮部族领地",
  @"Seal-tribe lands":@"海豹部族领地", @"Njerpez territory":@"Njerpez 领地",
  @"no man's land":@"无人区",
 };
 static NSDictionary* compass = @{
  @"northern":@"北部", @"north-eastern":@"东北部", @"eastern":@"东部",
  @"south-eastern":@"东南部", @"southern":@"南部", @"south-western":@"西南部",
  @"western":@"西部", @"north-western":@"西北部",
 };
 if (![area hasPrefix:@"in "]) return nil;
 area = [area substringFromIndex:3];
 NSString* translated = cultures[area];
 if (!translated) {
  for (NSString* direction in compass) {
   NSString* prefix = [direction stringByAppendingString:@" "];
   if (![area hasPrefix:prefix]) continue;
   NSString* culture = cultures[[area substringFromIndex:prefix.length]];
   if (culture) translated = [culture stringByAppendingString:compass[direction]];
   break;
  }
 }
 if (!translated && [area hasPrefix:@"no man's land "]) {
  for (NSString* direction in @[@"north", @"south", @"east", @"west"]) {
   NSString* prefix = [NSString stringWithFormat:@"no man's land %@ of ", direction];
   if (![area hasPrefix:prefix]) continue;
   NSString* culture = cultures[[area substringFromIndex:prefix.length]];
   if (culture) translated = [NSString stringWithFormat:@"%@以%@的无人区", culture, extraDirections()[direction]];
   break;
  }
 }
 if (!translated) return nil;
 return region ? [NSString stringWithFormat:@"那里位于%@，在名为 %@ 的地区。", translated, region]
               : [NSString stringWithFormat:@"那里位于%@。", translated];
}

#include "animal_dialogue.inc"
#include "blacksmith_dialogue.inc"
#include "local_dialogue.inc"

static NSString* composeExtraDialogue(NSString* source) {
 if (source.length > 1023) return nil;
 if (NSString* blacksmith = composeBlacksmithNpc(source)) return blacksmith;
 if (NSString* animal = composeAnimalDialogue(source)) return animal;
 if (NSString* local = composeLocalDialogue(source)) return local;
 static NSDictionary* exact = @{
  @"Not here, unfortunately.":@"可惜这里没有。",
  @"No, unfortunately not. And I'm afraid there isn't one nearby either.":@"可惜没有。附近恐怕也找不到贤者。",
  @"No, there are no blacksmiths around here. You will have to ask elsewhere.":@"这附近没有铁匠。你得到别处打听。",
  @"and timbercraft.":@"，伐木也是一样。",
  @"I'm a mere negotiator between the people and the spirit world.":@"我只是在人们和灵界之间传话。",
  @"I'm soothsayer old as time. I know more than I can even remember.":@"我这占卜者和岁月一样古老。我知道的事多得连自己都记不清。",
  @"Well, at least so far my powers and advises have assured welfare of the people here.":@"嗯，至少到现在，我的能力和忠告还保得这里的人平安。",
  @"The beard doesn't grow in a day.":@"胡子可不是一天长成的。",
  @"Well for one, I know songs to sink nosy youngsters into a bog.":@"比如说，我会唱几首歌，把爱打听的年轻人沉进沼泽。",
  @"Curious you may be, but my expertise is beyond your understanding.":@"你或许好奇，可我懂的东西超出了你的理解。",
  @"Hehehe...":@"呵呵呵……",
  @"Who has beard has the power.":@"有胡子的人就有力量。",
 };
 if (NSString* result = exact[source]) return result;

 static NSDictionary* levels = @{
  @"unskilled":@"一窍不通", @"untrained":@"没受过训练", @"amateur":@"只懂些皮毛",
  @"novice":@"刚入门", @"adequate":@"还算过得去", @"competent":@"能够胜任",
  @"skilled":@"很熟练", @"talented":@"颇有天赋", @"expert":@"十分精通",
  @"master":@"达到了大师水准", @"grandmaster":@"达到了宗师水准",
  @"skilled expert":@"技艺高超",
 };
 if (NSString* level = extraBetween(source, @"I'm ", @" in hideworking")) {
  NSString* grade = levels[level];
  return grade ? [NSString stringWithFormat:@"我在皮革加工方面%@", grade] : nil;
 }
 if (NSString* level = extraBetween(source, @"and ", @" with timbercraft.")) {
  NSString* grade = levels[level];
  return grade ? [NSString stringWithFormat:@"，伐木方面%@。", grade] : nil;
 }
 if (NSString* route = extraBetween(source, @"But ", @" there is a village with a sage.")) {
  NSString* where = extraRoute(route);
  return where ? [NSString stringWithFormat:@"不过，%@有个村子，那里有一位贤者。", where] : nil;
 }
 if (NSString* name = extraBetween(source, @"Yes. We have our ", @".")) {
  return [NSString stringWithFormat:@"有，我们这儿有 %@。", name];
 }
 if (NSString* reply = extraBetween(source, @"Yes. We are proud to have ", @" as our blacksmith.")) {
  for (NSString* level in @[@"grandmaster", @"master", @"expert"]) {
   NSString* name = extraBetween(reply, [level stringByAppendingString:@" "], @"");
   if (name) return [NSString stringWithFormat:@"有。能有 %@ 这样一位%@的铁匠，我们很自豪。", name, levels[level]];
  }
  return nil;
 }
 if (NSString* reply = extraBetween(source, @"Not here, but you can find a ", @".")) {
  auto parts = [reply componentsSeparatedByString:@" blacksmith in a village "];
  if (parts.count != 2) return nil;
  NSString* grade = levels[parts[0]];
  NSString* where = extraRoute(parts[1]);
  return grade && where ? [NSString stringWithFormat:@"这里没有。不过，%@有个村子，那里有一位%@的铁匠。", where, grade] : nil;
 }
 if (NSString* reply = extraBetween(source, @"I'm ", @" quality.")) {
  auto parts = [reply componentsSeparatedByString:@" in what I do, and my goods are of "];
  if (parts.count != 2) return nil;
  static NSDictionary* qualities = @{
   @"crude":@"粗糙", @"rough":@"粗制", @"decent":@"尚可", @"fine":@"精良", @"masterwork":@"大师级",
  };
  NSString* grade = levels[parts[0]], *quality = qualities[parts[1]];
  return grade && quality ? [NSString stringWithFormat:@"我的手艺%@，做出来的东西品质%@。", grade, quality] : nil;
 }
 return extraWorldLocation(source);
}

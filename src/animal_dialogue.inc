// AnimalDesc is a native creature name with an optional size adjective.
static NSDictionary* animalNames() {
 static NSDictionary* names = @{
  @"pig":@"猪", @"sow":@"母猪", @"boar":@"公猪",
  @"sheep":@"绵羊", @"ram":@"公羊", @"cow":@"母牛", @"bull":@"公牛",
  @"dog":@"狗", @"female dog":@"母狗", @"reindeer":@"驯鹿", @"horse":@"马",
  @"bull reindeer":@"雄驯鹿", @"reindeer doe":@"雌驯鹿",
  @"piglet":@"猪崽", @"lamb":@"羊羔", @"puppy":@"小狗",
  @"cow calf":@"牛犊", @"bull calf":@"公牛犊", @"reindeer calf":@"驯鹿幼崽",
  @"dog puppy":@"小狗",
 };
 return names;
}

static NSString* animalDescription(NSString* source) {
 NSString* name = [source lowercaseString];
 if (NSString* translated = animalNames()[name]) return translated;
 for (NSString* size in @[@"small ", @"big "]) {
  if (![name hasPrefix:size]) continue;
  NSString* translated = animalNames()[[name substringFromIndex:size.length]];
  if (translated) {
   NSString* adjective = [size isEqual:@"small "] ? @"小" : @"大";
   return [adjective stringByAppendingString:translated];
  }
 }
 return nil;
}

static NSString* composeAnimalDialogue(NSString* source) {
 NSString* list = extraBetween(source, @"We might have ", @" for sale, if you are interested.");
 if (list) {
  // The native andlist replaces the final comma with " and ".
  NSArray* tail = [list componentsSeparatedByString:@" and "];
  if (tail.count > 2 || [tail.lastObject containsString:@", "]) return nil;
  NSArray* animals = [[tail componentsJoinedByString:@", "] componentsSeparatedByString:@", "];
  if (animals.count > 5) return nil;
  NSMutableArray* translated = [NSMutableArray new];
  for (NSString* animal in animals) {
   NSString* name = animalDescription(animal);
   if (!name) return nil;
   [translated addObject:name];
  }
  return [NSString stringWithFormat:@"你要是有兴趣，我们这儿或许有%@可卖。", [translated componentsJoinedByString:@"、"]];
 }
 NSString* animal = extraBetween(source, @"You want that ", @"? Very well. Now make a trade and we'll see about that.");
 if (animal) {
  NSString* name = animalDescription(animal);
  return name ? [NSString stringWithFormat:@"你想买那只%@？好，你先出个价，我们再谈。", name] : nil;
 }
 animal = extraBetween(source, @"I'll get your ", @" here and also give you a rope so you can leash it.");
 if (animal) {
  NSString* name = animalDescription(animal);
  return name ? [NSString stringWithFormat:@"我去把你的%@牵过来，再给你一根绳子拴住它。", name] : nil;
 }
 return nil;
}

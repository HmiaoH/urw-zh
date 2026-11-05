// clang++ -fobjc-arc -framework Foundation tests/dialogue_extra.mm -o /tmp/dialogue_extra_test
#import <Foundation/Foundation.h>
#include <cassert>
#include "../src/dialogue_extra.inc"

int main() {
 @autoreleasepool {
  assert([composeExtraDialogue(@"At least a moment ago he was wandering around here in the north-west.")
          isEqual:@"至少刚才，他还在西北边转悠。"]);
  assert([composeExtraDialogue(@"A while ago she was inside just around the corner.")
          isEqual:@"刚才她还在拐角附近的屋子里。"]);
  assert([composeExtraDialogue(@"A while ago he was inside just nearby directly in the east.") containsString:@"正东"]);
  assert([composeExtraDialogue(@"She is right over there, behind your back.") isEqual:@"她就在你身后。"]);
  assert([composeExtraDialogue(@"He is right over there, you see.") isEqual:@"他就在那里，你看。"]);
  assert([composeExtraDialogue(@"I think she is around here, but I don't know where exactly.") containsString:@"具体在哪儿"]);
  assert([composeExtraDialogue(@"Our water supply is about 45 yards away in the north-west.") isEqual:@"我们的取水点在西北边约45码处。"]);
  assert([composeExtraDialogue(@"Our water supply is about 30 meters away directly in the south.") containsString:@"正南边约30米"]);
  assert([composeExtraDialogue(@"Our water supply is inside just around the corner in the north.") containsString:@"拐角处的屋里"]);
  assert([composeExtraDialogue(@"Our water supply is right over there in the west, you see.") containsString:@"西边"]);
  assert([composeExtraDialogue(@"Our water supply is directly in the east.") containsString:@"正东边"]);
  assert(!composeExtraDialogue(@"Our water supply is about 45 miles away in the north-west."));
  assert(!composeExtraDialogue(@"Our water supply is about 45 yards away in the left."));
  assert(!composeExtraDialogue(@"At least a moment ago the blacksmith was wandering around here in the north-west."));
  assert([composeExtraDialogue(@"We might have sheep for sale, if you are interested.")
          isEqual:@"你要是有兴趣，我们这儿或许有绵羊可卖。"]);
  assert([composeExtraDialogue(@"We might have big cow, sheep and small dog for sale, if you are interested.")
          isEqual:@"你要是有兴趣，我们这儿或许有大母牛、绵羊、小狗可卖。"]);
  assert([composeExtraDialogue(@"You want that small piglet? Very well. Now make a trade and we'll see about that.")
          isEqual:@"你想买那只小猪崽？好，你先出个价，我们再谈。"]);
  assert([composeExtraDialogue(@"I'll get your bull reindeer here and also give you a rope so you can leash it.")
          isEqual:@"我去把你的雄驯鹿牵过来，再给你一根绳子拴住它。"]);
  assert(!composeExtraDialogue(@"We might have cow and unknown for sale, if you are interested."));
  assert(!composeExtraDialogue(@"We might have cow, sheep, dog, sow, ram and pig for sale, if you are interested."));
  assert(!composeExtraDialogue(@"We might have cow and sheep, dog for sale, if you are interested."));
  assert(!composeExtraDialogue(@"I'll get your cow here tomorrow."));
  assert([composeExtraDialogue(@"I'm skilled in hideworking") isEqual:@"我在皮革加工方面很熟练"]);
  assert([composeExtraDialogue(@"and talented with timbercraft.") isEqual:@"，伐木方面颇有天赋。"]);
  assert(composeExtraDialogue(@"and timbercraft."));
  assert(composeExtraDialogue(@"I'm grandmaster in hideworking"));
  assert(!composeExtraDialogue(@"I'm unknown in hideworking"));
  assert(!composeExtraDialogue(@"I'm skilled in fishing"));
  assert(composeExtraDialogue(@"Not here, unfortunately."));
  assert([composeExtraDialogue(@"But in the south-west from here, just a couple of miles away there is a village with a sage.") containsString:@"西南，只有几英里"]);
  assert([composeExtraDialogue(@"It's in south-eastern Kuikka-tribe lands at the region called Nuokkukallio \"Nodcliff\".") containsString:@"Nuokkukallio \"Nodcliff\""]);
  assert([composeExtraDialogue(@"It's in Driik here at Äkäslompolo.") containsString:@"Äkäslompolo"]);
  assert(!composeExtraDialogue(@"It's in the kitchen."));
  assert(!composeExtraDialogue(@"But in the south-west from here, soon there is a village with a sage."));
  assert([composeExtraDialogue(@"Not here, but you can find a skilled expert blacksmith in a village directly in the east from here, about 9 kilometers away.") containsString:@"径直向东，约9公里"]);
  assert([composeExtraDialogue(@"Yes. We are proud to have master Matti as our blacksmith.") containsString:@"Matti"]);
  assert([composeExtraDialogue(@"Yes. We have our A. Matti.") containsString:@"A. Matti"]);
  assert(composeExtraDialogue(@"I'm master in what I do, and my goods are of masterwork quality."));
  assert(!composeExtraDialogue(@"I'm master in what I do, and my goods are of strange quality."));
 }
}

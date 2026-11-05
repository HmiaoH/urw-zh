// clang++ -fobjc-arc -framework Foundation tests/blacksmith_dialogue.mm -o /tmp/urw-blacksmith-test
#import <Foundation/Foundation.h>
#include <cassert>
#include "../src/dialogue_extra.inc"

static NSString* testPaymentItem(NSString* source) {
 return @{@"2 arrows":@"2 支箭", @"fine woollen shirt":@"精良羊毛衬衫", @"rye bread":@"黑麦面包"}[source];
}

int main() {
 @autoreleasepool {
  assert([composeTradePayment(@"rye bread.", testPaymentItem) isEqual:@"黑麦面包。"]);
  assert([composeTradePayment(@"2 arrows, fine woollen shirt (being worn) and rye bread.", testPaymentItem)
          isEqual:@"2 支箭、精良羊毛衬衫（正穿戴）、黑麦面包。"]);
  assert(!composeTradePayment(@"2 arrows and a mysterious tool.", testPaymentItem));
  assert(!composeTradePayment(@"2 arrows, rye bread.", testPaymentItem));
  assert(!composeTradePayment(@"2 arrows and rye bread", testPaymentItem));
  assert(!composeTradePayment(@"I think it's best if you make the offers now.", testPaymentItem));
  assert(blacksmithProducts().count == 31);
  for (NSString* item in blacksmithProducts()) {
   assert(composeBlacksmithPlayer([NSString stringWithFormat:@"\"I'd like to have a %@, please.\"", item]));
   assert(composeBlacksmithPlayer([NSString stringWithFormat:@"\"How's that fine %@ coming along?\"", item]));
   assert(composeExtraDialogue([NSString stringWithFormat:@"Very well. You shall have a masterwork %@.", item]));
   assert(composeExtraDialogue([NSString stringWithFormat:@"I'll get started with your %@, and expect to see you come claim it after half a week.", item]));
  }
  assert([composeBlacksmithPlayer(@"\"I'd like to have a sickle, please.\"") isEqual:@"“请帮我做一件镰刀。”"]);
  assert([composeBlacksmithPlayer(@"\"I'd like some iron fishhooks, please.\"") isEqual:@"“请帮我做一些铁鱼钩。”"]);
  assert([composeBlacksmithPlayer(@"\"How are those superior broadheads coming along?\"") containsString:@"上等宽头箭镞"]);
  assert([composeExtraDialogue(@"I can make you tools, knives, axes, spears, arrowheads, swords, a helmet and a shield.")
          isEqual:@"我能给你做工具、刀具、斧头、矛、箭镞、剑、头盔、盾牌。"]);
  assert([composeExtraDialogue(@"I can make you a sickle, a pot, a shovel, iron fishhooks and an iron sewing needle.")
          isEqual:@"我能给你做镰刀、锅、铲、铁鱼钩、铁缝衣针。"]);
  assert([composeExtraDialogue(@"Very well. You shall have a masterwork sickle.") isEqual:@"好，我会给你做大师级镰刀。"]);
  assert([composeExtraDialogue(@"Very well. You shall have 6 fine iron fishhooks.") isEqual:@"好，我会给你做6 个精良铁鱼钩。"]);
  assert([composeExtraDialogue(@"Very well. You shall have 12 superior arrowheads.") containsString:@"12 个上等箭镞"]);
  assert([composeExtraDialogue(@"It will take me a week to make it.") isEqual:@"我需要一周才能做好。"]);
  assert([composeExtraDialogue(@"It will take me few days to make them.") isEqual:@"我需要几天才能做好。"]);
  assert([composeExtraDialogue(@"I'll get started with your sickle, and expect to see you come claim it after a week.")
          isEqual:@"我这就开始做镰刀。一周后记得回来取。"]);
  assert([composeExtraDialogue(@"I'll get started with those iron fishhooks, and expect to see you come claim them after a week.")
          isEqual:@"我这就开始做铁鱼钩。一周后记得回来取。"]);
  assert([composeExtraDialogue(@"I'm working on it. Come ask again after 7 days.") containsString:@"7 天后"]);
  assert([composeExtraDialogue(@"It will be ready by early morning.") isEqual:@"清晨前就能做好。"]);
  assert([composeExtraDialogue(@"Your reward covers one fifth of this. The rest of it you have to pay.") containsString:@"五分之一"]);
  assert([composeExtraDialogue(@"I'm master in what I do, and my goods are of masterwork quality.") containsString:@"大师级"]);
  for (NSString* source in @[@"Very well. You shall have a horse.", @"Very well. You shall have 12 fine iron fishhooks.",
                             @"It will take me tomorrow to make it.", @"It will be ready after many days.",
                             @"I can make you an ango and some cake."])
   assert(!composeExtraDialogue(source));
  assert(!composeBlacksmithPlayer(@"\"I'd like to have a horse, please.\""));
 }
}

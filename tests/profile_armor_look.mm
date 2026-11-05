// clang++ -std=c++17 -fobjc-arc -framework Foundation tests/profile_armor_look.mm -o /tmp/profile_armor_look
#import <Foundation/Foundation.h>
#include <cassert>
#include <cstring>

struct TestState {
 NSDictionary* dictionary;
 NSDictionary* itemRules;
};
TestState& state(){static TestState s;return s;}

NSString* normalize(NSString* s){
 s=[[[s componentsSeparatedByCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]] filteredArrayUsingPredicate:[NSPredicate predicateWithFormat:@"length > 0"]] componentsJoinedByString:@" "];
 return [s stringByReplacingOccurrencesOfString:@"\\s*(</?[A-Za-z]+>)\\s*" withString:@"$1" options:NSRegularExpressionSearch range:NSMakeRange(0,s.length)];
}

#include "../src/items.inc"
NSString* matchTemplate(NSString*,NSString*){return nil;}

#include "../src/look_extra.inc"

id load(NSString* path){
 return [NSJSONSerialization JSONObjectWithData:[NSData dataWithContentsOfFile:path] options:0 error:nil];
}

int main(){
 @autoreleasepool {
  NSMutableDictionary* dictionary=[NSMutableDictionary new];
  for(NSDictionary* row in load(@"data/translations/profile_armor_look.json"))
   dictionary[[NSString stringWithFormat:@"%@\t%@",row[@"context"],normalize(row[@"original"])]]=row[@"translation"];
  state().dictionary=dictionary;
  state().itemRules=checkedItemRules(load(@"data/items.json"));
  assert(state().itemRules);
  NSString* capture=normalize(@"Kuikka-tribe girl. <br> <br> <blue> She is wearing <black> rough leather shoes and fine woollen undershirt. <br> <br>");

  assert([composeLook(capture,"paragraph") isEqual:@"库伊卡部族女孩。<br><br><blue>她穿着<black>粗制皮革鞋、精良羊毛内衫。<br><br>"]);
  assert([composeLook(@"Old kuikka-tribe man","showtext") isEqual:@"年老的库伊卡部族男子"]);
  assert([composeLook(@"#You see Kuikka-tribe girl there.","message") isEqual:@"你看见那里有一位库伊卡部族女孩。"]);
  assert([composeLook(@"Håkon the Driikiläis blacksmith","paragraph") isEqual:@"Håkon（德里克族铁匠）"]);

  assert(composeLook(@"Owl-tribe man.<br><br><red>He is wielding a longbow.<black><br><blue>He is wearing<black>leather shoes, fine woollen undershirt, and fur cap.<br><br>","paragraph"));
  NSString* elder=normalize(@"Old kuikka-tribe man. <br> <br> <blue> He is wearing <black> leather boots, fine leather trousers, woollen undershirt, fur overcoat and fine woollen footrags. <br> <br> <blue> He is carrying <black> fisher's knife and 3 dried squirrel cuts. <br>");
  assert([composeLook(elder,"paragraph") isEqual:@"年老的库伊卡部族男子。<br><br><blue>他穿着<black>皮革靴、精良皮革长裤、羊毛内衫、毛皮外套、精良羊毛裹脚布。<br><br><blue>他带着<black>渔刀、3 风干松鼠肉块。<br>"]);
  assert(!composeLook(@"Owl-tribe crocodile","showtext"));
  assert(!composeLook(@"Owl-tribe girl.<br><blue>She is wearing<black>leather shoes and unknown jacket.<br>","paragraph"));
  assert(!composeLook(@"Owl-tribe girl.<br><red>.<black>","paragraph"));
  assert(!composeLook(capture,"message"));
 }
}

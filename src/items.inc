// Only complete inventory labels enter this grammar. Unknown or ambiguous input
// fails closed; no English buffer, ItemStruct or save data is modified.
thread_local bool drawingItems=false;
bool inventoryList=false;
enum class ItemMeasure { None, Length, YarnBall };

static bool itemMeasureMatches(NSString* key,ItemMeasure measure){
 if(measure==ItemMeasure::None)return true;
 if([key isEqual:@"yarn"]||[key hasSuffix:@" yarn"])return true;
 return measure==ItemMeasure::Length&&
        ([key isEqual:@"hemp cloth"]||[key isEqual:@"linen cloth"]||
         [key isEqual:@"nettle cloth"]||[key isEqual:@"woollen cloth"]||[key isEqual:@"wool cloth"]||
         [key isEqual:@"rope"]||[key hasSuffix:@" rope"]||
         [key isEqual:@"cord"]||[key hasSuffix:@" cord"]||[key isEqual:@"bowstring"]);
}

NSString* itemBody(NSString* source,NSDictionary* rules,unsigned used=0,ItemMeasure measure=ItemMeasure::None){
 NSString* key=rules[@"plurals"][source]?:source;
 source=key;
 NSString* direct=rules[@"bases"][key];if(direct)return itemMeasureMatches(key,measure)?direct:nil;
 NSString* answer=nil;
 NSArray* groups=@[@"quality",@"material",@"state"];
 for(unsigned i=0;i<groups.count;i++){
  if(used&(1u<<i))continue;
  NSDictionary* group=rules[groups[i]];
  for(NSString* prefix in group){
   NSString* start=[prefix stringByAppendingString:@" "];
   if(![source hasPrefix:start])continue;
   NSString* tail=itemBody([source substringFromIndex:start.length],rules,used|(1u<<i),measure);
   if(!tail)continue;
   NSString* candidate=[group[prefix] stringByAppendingString:tail];
   if(answer&&![answer isEqual:candidate])return nil;
   answer=candidate;
  }
 }
 return answer;
}
NSString* composeItem(NSString* source){
 NSDictionary* rules=state().itemRules;if(!rules)return nil;
 NSString* s=[source lowercaseString];if(s.length>240||[s containsString:@".."]||[s containsString:@"\n"])return nil;
 NSMutableString* suffix=[NSMutableString new];
 for(int n=0;n<3;n++){
  NSString* found=nil;
  for(NSString* end in rules[@"suffix"])if([s hasSuffix:end]){if(found)return nil;found=end;}
  if(!found)break;
  [suffix insertString:rules[@"suffix"][found] atIndex:0];s=[s substringToIndex:s.length-found.length];
 }
 // ekuvaus adds a length from UnitString_Length before any trade suffix.
 static NSRegularExpression* measurement=[NSRegularExpression
  regularExpressionWithPattern:@" \\(([0-9]{1,9}(?:\\.[0-9]{1,2})?) (ft|in|m|cm)\\)\\z" options:0 error:nil];
 static NSDictionary* units=@{@"ft":@"英尺",@"in":@"英寸",@"m":@"米",@"cm":@"厘米"};
 NSString* length=@"";
 auto match=[s hasSuffix:@")"]?[measurement firstMatchInString:s options:0 range:NSMakeRange(0,s.length)]:nil;
 if(match){
  NSString* value=[s substringWithRange:[match rangeAtIndex:1]];
  NSString* unit=[s substringWithRange:[match rangeAtIndex:2]];
  length=[NSString stringWithFormat:@"（%@ %@）",value,units[unit]];
  s=[s substringToIndex:match.range.location];
 }
 NSString* count=@"";
 NSRange number=[s rangeOfString:@"\\A[1-9][0-9]{0,8} " options:NSRegularExpressionSearch];
 if(number.location!=NSNotFound){count=[s substringWithRange:number];s=[s substringFromIndex:NSMaxRange(number)];}
 ItemMeasure measure=match?ItemMeasure::Length:ItemMeasure::None;
 if(match){
  NSString* ball=[s hasPrefix:@"ball of "]?@"ball of ":@"balls of ";
  if([s hasPrefix:ball]){
   measure=ItemMeasure::YarnBall;
   s=[s substringFromIndex:ball.length];
  }
 }
 NSString* body=itemBody(s,rules,0,measure);if(!body)return nil;
 // Harvest resources define these package forms as full reviewed bases.
 if(!count.length&&([s hasPrefix:@"fistful of "]||[s hasPrefix:@"bunch of "]||[s hasPrefix:@"pinch of "]))count=@"一";
 NSString* ball=@"";
 if(measure==ItemMeasure::YarnBall)ball=count.length?@"团":@"一团";
 return [NSString stringWithFormat:@"%@%@%@%@%@",count,ball,body,length,suffix];
}

NSDictionary* checkedItemRules(id rules){
 if(![rules isKindOfClass:[NSDictionary class]]||![rules[@"schema"] isEqual:@1])return nil;
 for(NSString* group in @[@"bases",@"plurals",@"quality",@"material",@"state",@"suffix"]){
  id pairs=rules[group];if(![pairs isKindOfClass:[NSDictionary class]]||[pairs count]>2000)return nil;
  for(id key in pairs){id value=pairs[key];
   if(![key isKindOfClass:[NSString class]]||![value isKindOfClass:[NSString class]]||![key length]||![value length]||[key length]>240||[value length]>240)return nil;
  }
 }return rules;
}

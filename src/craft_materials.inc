// Esita_Tarvikelista emits whole material rows with a bounded native
// quantity, total, and optional length or weight. Preserve every value.
NSString* composeCraftMaterialLabel(NSString* source){
 if(!source.length||source.length>240)return nil;
 static NSRegularExpression* format=[NSRegularExpression regularExpressionWithPattern:
  @"\\A(?:([0-9]{1,9}(?:[.][0-9]{1,3})?) (ft|in|m|cm|lbs?|oz|kg|g)(?: of)? )?(.+?)(?: \\* ([1-9][0-9]{0,8}))?(?: \\(of ([1-9][0-9]{0,8})\\))?\\z"
  options:0 error:nil];
 auto match=[format firstMatchInString:source options:0 range:NSMakeRange(0,source.length)];
 if(!match)return nil;
 auto field=[&](int slot)->NSString*{
  NSRange range=[match rangeAtIndex:slot];
  return range.location==NSNotFound?nil:[source substringWithRange:range];
 };
 NSString* name=craftIngredient([field(3) lowercaseString]);
 if(!name)return nil;
 NSString* measure=field(1);
 NSString* count=field(4);
 NSString* total=field(5);
 if(total&&!count)return nil;
 NSMutableString* out=[NSMutableString new];
 if(measure){
  static NSDictionary* units=@{@"ft":@"英尺",@"in":@"英寸",@"m":@"米",@"cm":@"厘米",
   @"lb":@"磅",@"lbs":@"磅",@"oz":@"盎司",@"kg":@"千克",@"g":@"克"};
  [out appendFormat:@"%@ %@ ",measure,units[field(2)]];
 }
 [out appendString:name];
 if(count)[out appendFormat:@" × %@",count];
 if(total)[out appendFormat:@"（共 %@）",total];
 return out;
}

#include "craft_skill_options.inc"

NSString* composeCraftSubmenuNote(NSString* source){
 if(NSString* note=notificationSpan(source,@"_(",@")")){
  NSString* explanation=state().dictionary[[@"craft-explanation\t" stringByAppendingString:note]];
  if(explanation)return [NSString stringWithFormat:@"（%@）",explanation];
 }
 if(![source hasPrefix:@"#"])return nil;
 NSRange colon=[source rangeOfString:@": "];
 if(colon.location==NSNotFound||colon.location<=1)return nil;
 NSString* header=[source substringWithRange:NSMakeRange(1,colon.location-1)];
 NSString* title=state().dictionary[[@"craft-menu-heading\t" stringByAppendingString:[header uppercaseString]]];
 if(!title)return nil;
 NSString* recipe=[source substringFromIndex:NSMaxRange(colon)];
 NSString* name=state().dictionary[[@"craft-recipe\t" stringByAppendingString:recipe]]?:composeCraftPiecesLabel(recipe);
 return name?[NSString stringWithFormat:@"%@：%@",title,name]:nil;
}

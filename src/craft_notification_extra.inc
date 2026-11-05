// Shared crafting notifications keep the requirement number and use the
// existing full item matcher for selected tools and quality descriptions.
NSString* craftIngredient(NSString* source){
 return state().dictionary[[@"craft-ingredient\t" stringByAppendingString:source]]?:messageItem(source);
}

#include "craft_materials.inc"

NSString* craftRequirement(NSString* source){
 NSString* body=notificationSpan(source,@"?(",@".");
 if(!body)return nil;
 NSRange marker=[body rangeOfString:@") "];
 if(marker.location==NSNotFound)return nil;
 NSString* index=[body substringToIndex:marker.location];
 if([index rangeOfString:@"\\A[1-9][0-9]{0,2}\\z" options:NSRegularExpressionSearch].location==NSNotFound)return nil;
 NSString* remainder=[body substringFromIndex:NSMaxRange(marker)];
 bool optional=[remainder hasPrefix:@"You may optionally use "];
 NSString* lead=optional?@"You may optionally use ":@"You need ";
 if(![remainder hasPrefix:lead])return nil;
 NSArray<NSString*>* parts=[[remainder substringFromIndex:lead.length] componentsSeparatedByString:@" - preferably "];
 if(parts.count>2)return nil;
 NSString* item=composeCraftMaterialLabel(parts[0]);
 if(!item)return nil;
 NSString* requirement=[NSString stringWithFormat:@"（%@）%@%@",index,optional?@"可选用":@"需要",item];
 if(parts.count==1)return [requirement stringByAppendingString:@"。"];
 NSString* preferred=messageItem(parts[1]);
 return preferred?[NSString stringWithFormat:@"%@，最好用%@。",requirement,preferred]:nil;
}

NSString* composeCraftNotification(NSString* source){
 if(NSString* menu=composeCraftSubmenuNote(source))return menu;
 if(NSString* requirement=craftRequirement(source))return requirement;
 static NSArray* toolForms=@[
  @[@"+",@" in your inventory will be used.",@"将使用你携带的%@。"],
  @[@"+",@" nearby will be used.",@"将使用附近的%@。"],
  @[@"Ok. ",@" you have will be used.",@"将使用你已有的%@。"]
 ];
 for(NSArray<NSString*>* form in toolForms){
  NSString* raw=notificationSpan(source,form[0],form[1]);
  if(!raw)continue;
  if(NSString* item=messageItem(raw))return [NSString stringWithFormat:form[2],item];
 }
 static NSArray* qualityForms=@[
  @[@"!",@" is the right tool here but suffers from ",@" quality.",@"%@适合这项工作，但品质为%@。"],
  @[@"=",@" is the right tool here and its ",@" quality certainly helps.",@"%@适合这项工作，%@品质也有帮助。"],
  @[@"+",@" is the right tool here and its ",@" quality certainly helps.",@"%@适合这项工作，%@品质也有帮助。"]
 ];
 for(NSArray<NSString*>* form in qualityForms){
  NSString* raw=notificationSpan(source,form[0],form[2]);
  NSArray<NSString*>* parts=[raw componentsSeparatedByString:form[1]];
  if(parts.count!=2)continue;
  NSString* item=messageItem(parts[0]),*quality=state().itemRules[@"quality"][parts[1]];
  if(item&&quality)return [NSString stringWithFormat:form[3],item,quality];
 }
 return nil;
}

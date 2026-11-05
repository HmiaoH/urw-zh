// The native recipe menu appends a yield to an otherwise complete recipe
// name. Only translate a numeric suffix on a reviewed recipe.
NSString* composeCraftPiecesLabel(NSString* source){
 if(!source.length||source.length>180)return nil;
 NSString* body=notificationSpan(source,@"",@" pieces)");
 if(!body)return nil;
 NSRange separator=[body rangeOfString:@" (" options:NSBackwardsSearch];
 if(separator.location==NSNotFound||!separator.location)return nil;
 NSString* count=[body substringFromIndex:NSMaxRange(separator)];
 if([count rangeOfString:@"\\A[1-9][0-9]{0,8}\\z" options:NSRegularExpressionSearch].location==NSNotFound)return nil;
 NSString* key=[body substringToIndex:separator.location];
 NSString* name=state().dictionary[[@"craft-recipe\t" stringByAppendingString:key]];
 return name?[NSString stringWithFormat:@"%@（%@ 件）",name,count]:nil;
}

 NSArray* courses=[NSJSONSerialization JSONObjectWithData:[NSData dataWithContentsOfFile:@"data/catalog/course_runtime.json"] options:0 error:nil];
 assert(courses.count==193);
 for(NSDictionary* row in courses){
  NSString* context=row[@"context"];
  NSString* z=zh::translate([row[@"original"] UTF8String],context.UTF8String);
  assert(z&&z.length);
  if([context isEqual:@"paragraph"]){
   auto paragraph=zh::layoutParagraph(z,440,{255,255,255,255});
   int limit=[row[@"part"] isEqual:@"current"]?155:[row[@"part"] isEqual:@"completed"]?120:105;
   for(auto& run:paragraph.runs){assert(run.x+run.w<=440);assert(run.y+12<=limit);}
  }
 }
 assert([zh::translate("GREETING THE EARTH UPON GOING TO SLEEP","showtext") isEqual:@"入睡时向大地致意"]);

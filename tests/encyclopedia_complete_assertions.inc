 // Walk each source page in native order, retaining paragraph gaps and link hit regions.
 NSDictionary* encyclopediaAudit=zh::json(@"data/rules/encyclopedia_coverage.json");
 NSString* checkedTopic=nil;int pageX=60,pageY=60,lastSourceLine=0,linkCount=0;bool pageOk=true;int layoutFailures=0;
 for(NSDictionary* fragment in encyclopediaAudit[@"fragments"]){
  NSString* topic=fragment[@"topic"];int line=[fragment[@"line"] intValue];
  if(![checkedTopic isEqual:topic]){checkedTopic=topic;pageX=60;pageY=60;lastSourceLine=line;linkCount=0;pageOk=true;}
  if(!pageOk)continue;
  if(line>lastSourceLine+1){pageX=60;pageY+=24*(line-lastSourceLine-1);}lastSourceLine=line;
  auto z=zh::translate([fragment[@"original"] UTF8String],"encyclopedia");
  if(!z)continue; // Coverage completeness has a separate source audit.
  auto layout=zh::hyperLayout([z stringByReplacingOccurrencesOfString:@"<br>" withString:@"\n"],pageX,pageY);
  for(auto& run:layout.runs)if(run.target)++linkCount;
  if(!layout.valid||linkCount>=99){fprintf(stderr,"encyclopedia layout: %s line %d y=%d links=%d\n",topic.UTF8String,line,pageY,linkCount);++layoutFailures;pageOk=false;continue;}
  pageX=layout.x;pageY=layout.y;
 }
 assert(layoutFailures==0);
 NSArray* completeRows=zh::json(@"data/translations/encyclopedia_complete.json");
 int previewFailures=0;
 for(NSDictionary* row in completeRows){
  if(![row[@"context"] isEqual:@"encyclopedia-summary"])continue;
  auto width=zh::bitmap(row[@"translation"],4096,{255,255,255,255}).w/2;
  if(width>424)fprintf(stderr,"encyclopedia preview too wide: %s width=%d\n",[row[@"original"] UTF8String],width);
  if(width>424)++previewFailures;
 }
 assert(previewFailures==0);

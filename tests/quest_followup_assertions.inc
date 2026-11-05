{
 assert([zh::composeItem(@"2 pinches of dull leaves") isEqual:@"2 撮暗淡的叶片"]);
 assert([zh::composeItem(@"pinch of dull leaves") isEqual:@"一撮暗淡的叶片"]);
 assert(zh::translate("#You see a patch of 5 growing dull grasses here.","message"));
 assert(zh::translate("!The dull grass here isn't ripe yet, but there are young leaves already.","message"));
 assert(zh::translate("#Gathering dull grass...","message"));
 assert(zh::translate(":You got 2 pinches of dull leaves.","message"));
 assert(zh::translate("It's plain good dull leaves and happily consumed too.","message"));
 assert(zh::translate("Assigned yesterday, expires in 29 days.","renshow"));
 assert([zh::questSentence(@"If you could bring me 40 fistfuls of bogbean leaves I would be very grateful.") containsString:@"40 把睡菜叶"]);
 assert(!zh::questSentence(@"If you could bring me 40 unknown magic items I would be very grateful."));
 NSString* q=@"\"My store of healing herbs is growing low, but my duties around here leave me with too little time go out on my clumsy legs and gather everything I need. If you know the local herbs and have the time, perhaps you would like to help me out and go find a little something I'm short of?\"<br><br>\"If you could bring me 40 fistfuls of bogbean leaves I would be very grateful.\"<br><br>";
 NSString* z=zh::translate(q.UTF8String,"paragraph");
 assert(z&&[z containsString:@"40 把睡菜叶"]&&[z containsString:@"库存"]);
 auto layout=zh::layoutParagraph(z,760,{0,0,0,255});assert(layout.height<250);
 assert(!zh::composeQuest(@"\"unknown player authored entry\"<br><br>","paragraph"));
}

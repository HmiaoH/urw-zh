#define URW_ZH_TEST
#include "../src/runtime.mm"
#include <cassert>
int main(){@autoreleasepool{
 auto hyper=zh::hyperLayout(@"用于[[HUNTING|狩猎]]的[[KNIFE|刀]]。",60,60,60,110);
 assert(hyper.valid);NSMutableString* visible=[NSMutableString new];int links=0;
 for(auto& run:hyper.runs){assert(run.x>=60&&run.x+run.w<=110);[visible appendString:run.text];if(run.target){++links;assert([run.target isEqual:@"HUNTING"]||[run.target isEqual:@"KNIFE"]);}}
 assert(links==2);assert([visible isEqual:@"用于狩猎的刀。"]);
 assert(!zh::hyperLayout(@"[[BAD|broken",60,60).valid);
 assert(!zh::hyperLayout(@"这是超出显示范围的长文",60,500,60,80).valid);
 assert([zh::decode("\xe4\xc4") isEqual:@"äÄ"]);
 assert([zh::decode("中文") isEqual:@"中文"]);
 auto finnish=zh::hyperTargetBytes(@"TIETÄJÄ");
 const unsigned char finnishTarget[]={84,73,69,84,142,74,142};
 assert(finnish.length==7&&!memcmp(finnish.bytes,finnishTarget,7));
 assert(zh::hyperLayout(@"[[TIETÄJÄ|贤者]]",60,60).valid);
 zh::loadCatalog();
 #include "trade_rejection_assertions.inc"
 #include "encyclopedia_complete_assertions.inc"
 NSArray* encyclopediaRows=[NSJSONSerialization JSONObjectWithData:[NSData dataWithContentsOfFile:@"data/translations/encyclopedia_materials.json"] options:0 error:nil];
 assert(encyclopediaRows.count>0);
 NSArray* fishRows=[NSJSONSerialization JSONObjectWithData:[NSData dataWithContentsOfFile:@"data/translations/encyclopedia_fish_tools.json"] options:0 error:nil];
 NSMutableArray* combined=[encyclopediaRows mutableCopy];
 for(NSDictionary* row in fishRows)if([row[@"context"] isEqual:@"encyclopedia"])[combined addObject:row];
 encyclopediaRows=combined;
 NSArray* summaries=[NSJSONSerialization JSONObjectWithData:[NSData dataWithContentsOfFile:@"data/translations/encyclopedia_summaries.json"] options:0 error:nil];
 for(NSDictionary* row in summaries){
  assert(zh::translate([row[@"original"] UTF8String],[row[@"context"] UTF8String]));
  assert(zh::bitmap(row[@"translation"],4096,{255,255,255,255}).w/2<=424);
 }
 NSString* page=nil;int hx=60,hy=60,pageLinks=0,previousLine=0;
 for(NSDictionary* row in encyclopediaRows){
  NSString* topic=row[@"evidence"][@"topic"];
  int sourceLine=[row[@"evidence"][@"line"] intValue];
  if(![page isEqual:topic]){page=topic;hx=60;hy=60;pageLinks=0;previousLine=sourceLine;}
  // Allow two native rows for each intervening blank resource line.
  if(sourceLine>previousLine+1){hx=60;hy+=24*(sourceLine-previousLine-1);}
  previousLine=sourceLine;
  NSString* translated=zh::translate([row[@"original"] UTF8String],"encyclopedia");assert(translated);
  auto layout=zh::hyperLayout([translated stringByReplacingOccurrencesOfString:@"<br>" withString:@"\n"],hx,hy);
  assert(layout.valid);
  for(auto& run:layout.runs)if(run.target)++pageLinks;
  assert(pageLinks<99);hx=layout.x;hy=layout.y;
 }
 #include "notification_followup_assertions.inc"
 #include "inventory_map_followup_assertions.inc"
 #include "craft_followup_assertions.inc"
 #include "craft_submenu_assertions.inc"
 #include "craft_skill_menu_assertions.inc"
 assert([zh::composeItem(@"perfect hemp cloth (6 ft)") isEqual:@"完美大麻布（6 英尺）"]);
 assert([zh::composeItem(@"2 paddles") isEqual:@"2 船桨"]);
 assert(zh::composeItem(@"paddle (6 ft)")==nil);
 #include "course_assertions.inc"
 zh::previewTopic="FUR";
 assert([zh::previewTranslation(15,563) length]>0);
 assert(zh::previewTranslation(15,562)==nil);
 zh::previewHasCustomText=true;assert(zh::previewTranslation(15,563)==nil);
 zh::previewHasCustomText=false;zh::previewTopic.clear();
 assert([zh::composeItem(@"4 slender pine trunks") isEqual:@"4 细松树干"]);
 assert([zh::translate("Bitterly cold","status-warmth") length]>0);
 assert(zh::statusTextContextAt(0x100130fc7ULL)!=nullptr);
 assert(zh::statusTextContextAt(0x100130fc8ULL)==nullptr);
 assert(zh::checkedItemRules(@[])==nil);
 assert(zh::checkedItemRules(@{@"schema":@1,@"bases":@[]})==nil);
 assert(zh::state().itemRules);
 assert([zh::composeItem(@"wolf fur") isEqual:@"狼毛皮"]);
 assert([zh::composeItem(@"2 reindeer furs") isEqual:@"2 驯鹿毛皮"]);
 assert([zh::composeItem(@"nettle yarn (200 ft)") isEqual:@"荨麻纱线（200 英尺）"]);
 assert([zh::composeItem(@"smoked lavaret") isEqual:@"烟熏白鲑"]);
 assert(zh::composeItem(@"hunting knife (200 ft)")==nil);
 assert([zh::composeMessage(@"+The rough woodsman's axe wielded as a primary weapon.") isEqual:@"已将粗制伐木斧用作主要武器。"]);
 assert([zh::composeMessage(@"#You see 7 wooden stakes here.") containsString:@"7 木制桩"]);
 assert(zh::composeMessage(@"#You see an unknown relic here.")==nil);
 assert([zh::composeMessage(@"!There's a western wall of a kota blocking your way!") containsString:@"西侧帐壁"]);
 assert(zh::composeExtraDialogue(@"and talented with timbercraft."));
 assert(zh::translateMapLocation(@"Pine mire at Jouhilaki \"Horsehair summit\""));
 assert([zh::translateMapLocation(@"Pahtolaki \"Cliffen summit\"") isEqual:@"Pahtolaki 「峭岩峰」"]);
 assert([zh::translateQuotedMapGloss(@"\"Block mountains\"") isEqual:@"「方石群山」"]);
 assert([zh::translateQuotedMapGloss(@"\"Nodcliff\"") isEqual:@"「点头崖」"]);
 assert([zh::translateMapRegion(@"Eastern Kuikka-tribe lands") isEqual:@"库伊卡部族领地 · 东部"]);
 assert([zh::translateMapRegion(@"South-eastern Kuikka-tribe lands") hasSuffix:@"东南部"]);
 assert(!zh::translateMapGloss(@"Cliffensummit"));
 assert(!zh::translateMapLocation(@"Äkäslompolo \"Invented title\""));
 assert(!zh::translateMapLocation(@"Äkäslompolo"));
 assert([zh::translate("Late morning","showtext") isEqual:@"临近中午"]);
 assert([zh::memorialDate(@"She faced her end in summer season, during beginning of Fallow month, on day 6 of 7th week before midsummer point.")
  isEqual:@"她于夏季休耕月初（仲夏前第 7周第 6 天）去世。"]);
 assert([zh::memorialDate(@"He faced his end in winter season, during late Pearl month, on 22nd of month:2.") containsString:@"2 月 22 日"]);
 assert([zh::memorialPlace(@"River at Tapionvirta \"Tapio's stream\" in north-eastern Kuikka-tribe lands became the place of her death. There she drowned after fainting in the freezing water.") containsString:@"Tapionvirta 「塔皮奥之溪」"]);
 assert([zh::translate("She died at 16 winters old, having spent 1 days of adventuring life.","showtext") isEqual:@"她去世时16岁，历险1天。"]);
 assert([zh::memorialCauseCaption(@"Drowned after fainting in the freezing water.") isEqual:@"在冰冷的水中昏迷后溺亡。"]);
 assert(zh::translate("Kaumolainen","showtext")==nil);
 zh::drawingProfileName=true;
 assert([zh::composeMemorial(@"Test Kaumolainen","showtext") isEqual:@"Test · 考莫族"]);
 zh::drawingProfileName=false;
 assert([zh::composeItem(@"2 fine woodsman's axes") isEqual:@"2 精良伐木斧"]);
 assert([zh::composeItem(@"3 blocks of wood") isEqual:@"3 木块"]);
 assert([zh::composeItem(@"3 fine woollen shirts") isEqual:@"3 精良羊毛衬衫"]);
 assert([zh::composeItem(@"2 rough fur boots (unpaid)") isEqual:@"2 粗制毛皮靴（未付款）"]);
 assert([zh::composeItem(@"rotten roasted elk cut") isEqual:@"腐烂烤驼鹿肉块"]); // Explicit condition + preparation combinations.
 assert([zh::composeItem(@"masterwork hunting knife") isEqual:@"大师级猎刀"]);
 assert([zh::composeItem(@"12 smoked hazel grouse cuts") isEqual:@"12 烟熏榛鸡肉块"]);
 assert([zh::composeItem(@"inferior wooden shovel") isEqual:@"劣质木制铲"]);
 for(NSString* bad in @[@"Mielus Kaumolainen",@"fine unknown sword",@"fine fine knife",@"knife of Mielus",@"rough woollen undersh..",@"-2 arrows",@"2.5 arrows",@"0 arrows",@"You have a fine knife.",@"knife (mysterious)"])
  assert(zh::composeItem(bad)==nil);
 for(NSString* quality in zh::state().itemRules[@"quality"])
  for(NSString* material in @[@"linen",@"woollen",@"leather",@"fur"])
   for(NSString* count in @[@"",@"2 ",@"999 "]){
    NSString* value=[NSString stringWithFormat:@"%@%@ %@ shirt (taken)",count,quality,material];
    auto output=zh::composeItem(value);assert(output);assert(!count.length||[output hasPrefix:count]);assert([output hasSuffix:@"（已取用）"]);
   }
 assert(zh::translate("masterwork hunting knife","showtext")==nil);
 zh::drawingItems=true;
 assert([zh::translate("masterwork hunting knife","showtext") isEqual:@"大师级猎刀"]);
 assert(zh::translate("masterwork hunting knife","message")==nil);
 zh::drawingItems=false;
 assert([zh::translate("6 fine iron fishhooks and rye bread.","npc-talk",true) containsString:@"铁鱼钩"]);
 assert(zh::translate("6 fine iron fishhooks and rye bread.","npc-talk")==nil);
 assert([zh::translate("\"I'd like to have a sickle, please.\"","player-talk") containsString:@"镰刀"]);
 assert([zh::translate("Chatting with Another the Kuikka-tribe Woman","showtext") isEqual:@"正在与 Another（库伊卡部族女子） 交谈"]);
 assert([zh::translate("Chatting with Driikiläis blacksmith","showtext") isEqual:@"正在与 德里克族铁匠 交谈"]);
 assert([zh::translate("Chatting with Soini the Driikiläis craftsman","showtext") isEqual:@"正在与 Soini（德里克族工匠） 交谈"]);
 assert([zh::translate("Chatting with an unknown traveler","showtext") isEqual:@"正在与 an unknown traveler 交谈"]);
 assert([zh::translate("It is driikiläis village.","npc-talk") isEqual:@"那是德里克族的村庄。"]);
 assert([zh::translate("Our water supply is about 45 yards away in the north-west.","npc-talk") isEqual:@"我们的取水点在西北边约45码处。"]);
 assert([zh::translate("At least a moment ago he was wandering around here in the north-west.","npc-talk") isEqual:@"至少刚才，他还在西北边转悠。"]);
 assert(zh::translate("\"Where is your village water supply?\"","player-talk"));
 assert([zh::translate("There is a settlement in the south-west at the region called Nuokkukallio \"Nodcliff\".","npc-talk") containsString:@"Nuokkukallio \"Nodcliff\""]);

 assert([zh::translate("There is a lake in the north-east here at Testplace.","npc-talk") isEqual:@"就在这一带的 Testplace，往东北方有一片湖泊。"]);
 assert([zh::translate("It is about 12 miles away.","npc-talk") isEqual:@"离这里约12英里。"]);
 assert(zh::translate("There is a tower in the north-east here at Testplace.","npc-talk")==nil);
 const char* prompt="Use hotkeys, mouse click or .ENTER to select.";
 auto parts=zh::segments(prompt,"showtext");assert(parts.count==2);
 assert(zh::segments(prompt,"renshow")==nil);
 std::vector<uint32_t> pixels(800*40,0);
 SDL_Surface* canvas=SDL_CreateRGBSurfaceFrom(pixels.data(),800,40,32,800*4,0xff,0xff00,0xff0000,0xff000000);
 assert(canvas);zh::state().screen=&canvas;
 assert(zh::drawTranslated(0,10,zh::translate(prompt,"showtext"),SDL_MapRGB(canvas->format,255,255,255),400,prompt,"showtext"));
 bool prefix=false,suffix=false;
 for(int y=0;y<40;y++)for(int x=0;x<800;x++){
  if(x>=216&&x<272)assert(pixels[y*800+x]==0); // Original ENTER keycap owns this gap.
  if(pixels[y*800+x]){if(x<216)prefix=true;if(x>=272)suffix=true;}
 }
 assert(prefix&&suffix);
 // Notification replacement must stay in exactly the cleared native row, and
 // repeated original word draws must not paint a second copy of the translation.
 std::fill(pixels.begin(),pixels.end(),0);SDL_Rect noteBox{0,0,300,40};
 auto& ns=zh::state();ns.noteBox=&noteBox;ns.lineHeight=+[](float){return 10;};
 char originalNote[]="!That is not a door or gate.";ns.noteText=originalNote;
 zh::NoteFrame nf;zh::activeNote=&nf;
 assert(zh::prepareNote(5,25,SDL_MapRGB(canvas->format,168,0,0)));assert(nf.painted);
 auto once=pixels;assert(zh::prepareNote(75,25,SDL_MapRGB(canvas->format,168,0,0)));assert(once==pixels);
 bool painted=false;
 for(int yy=0;yy<40;yy++)for(int xx=0;xx<800;xx++)if(pixels[yy*800+xx]){painted=true;assert(yy>=25&&yy<35&&xx>=5&&xx<295);}
 assert(painted);assert(!strcmp(originalNote,"!That is not a door or gate."));
 // Native fading treats ANY non-background RGB as ink: no fractional halo may survive.
 for(uint32_t pixel:pixels)if(pixel){uint8_t r,g,b;SDL_GetRGB(pixel,canvas->format,&r,&g,&b);assert(r==168&&g==0&&b==0);}
 assert(!zh::drawNoteRow(5,25,@"这是一条无法放入狭窄单行区域的长通知",0,20,10));
 for(NSString* glyph in @[@"你",@"看",@"麦",@"熟",@"药",@"蘑"]){
  auto mask=zh::messageRowRaster(glyph,{20,50,112,255},40,10,true);
  auto smooth=zh::messageRowRaster(glyph,{20,50,112,255},40,10,false);
  assert(mask.h==10&&mask.w>0);int occupiedRows=0,ink=0;bool fractional=false;
  for(int y=0;y<10;y++){bool occupied=false;
   for(int x=0;x<mask.w;x++){
    auto a=mask.pixels[(y*mask.w+x)*4+3];assert(a==0||a==255);
    if(a){occupied=true;++ink;}
    auto aa=smooth.pixels[(y*smooth.w+x)*4+3];if(aa&&aa<255)fractional=true;
   }
   if(occupied)++occupiedRows;
  }
  assert(occupiedRows>=9&&ink>=20&&fractional);
 }

 zh::activeNote=nullptr;ns.noteBox=nullptr;ns.noteText=nullptr;ns.lineHeight=nullptr;
 const char* saved="Your character has been saved.";
 const char* savedFormat="(008000):16g8:[=]{04FF0214}      ";
 auto logKey=zh::messageLogKey(saved,savedFormat);
 assert([logKey isEqual:@"=Your character has been saved."]);
 assert(zh::messageLogKey(saved,"(600060):16g8:[\"]{04FF0214}      ")==nil);
 assert(zh::messageLogKey(saved,"bad metadata")==nil);
 auto lookKey=zh::messageLogKey("You see 7 wooden stakes here.","(143270):16g8:[#]{04FF0214}      ");
 assert([zh::translate(lookKey.UTF8String,"message") containsString:@"7 木制桩"]);
 assert([zh::translateMessageLogRecord({"3 blocks of wood","(000000):16g8:[3]{04FF0214}      "}) isEqual:@"3 木块"]);
 assert([zh::translate("2-9 (of 9)","message-log-ui") isEqual:@"第 2–9 条（共 9 条）"]);
 NSString* logLong=@"这是一条较长的历史消息，跨行显示时应保留所有文字。";
 auto wrappedLog=zh::messageLogLines(logLong,65,2);
 assert(wrappedLog.size()==2);
 assert([[wrappedLog[0] stringByAppendingString:wrappedLog[1]] isEqual:logLong]);
 auto oneRow=zh::messageLogLines(logLong,65,1);
 assert(oneRow.size()==1&&[oneRow[0] isEqual:logLong]);
 std::fill(pixels.begin(),pixels.end(),0);
 zh::inMessageLog=true;
 zh::messageLogRecord={saved,savedFormat};
 auto measureLog=+[](int,int,int,int height,unsigned,int){assert(height==-1);return 0;};
 assert(zh::renderMessageLogRecord(measureLog,5,20,300,10,SDL_MapRGB(canvas->format,0,128,0),0)==0);
 zh::inMessageLog=false;
 bool logPainted=false;
 for(int yy=0;yy<40;yy++)for(int xx=0;xx<800;xx++)if(pixels[yy*800+xx]){
  logPainted=true;
  assert(yy>=20&&yy<30&&xx>=5&&xx<305);
  uint8_t r,g,b;SDL_GetRGB(pixels[yy*800+xx],canvas->format,&r,&g,&b);
  assert(!r&&!b&&g<=128);
 }
 assert(logPainted);
 SDL_FreeSurface(canvas);zh::state().screen=nullptr;
 assert([zh::translate("=Your character has been saved.","message") isEqual:@"角色已保存。"]);
 auto sample=@"<br><br>At the age of sixteen you left your home not only with some clothes, weapons and necessary equipment but also with some valuable seeds. <br>When you find a nice place to settle down you can start growing your own crops. (You have some turnip seeds, peas and a shovel with you. That's everything needed to try growing your own crops.)<br>";
 assert([zh::translate(sample.UTF8String,"paragraph") hasPrefix:@"<br><br>"]);
 assert([zh::translate(sample.UTF8String,"paragraph") hasSuffix:@"<br>"]);
 assert(zh::translate(sample.UTF8String,"showtext")==nil);
 assert(zh::translate([[sample stringByAppendingString:@" extra text"] UTF8String],"paragraph")==nil);
 auto z=zh::matchTemplate(@"Day 6 of 7th week before midsummer point",@"showtext");
 assert([z isEqual:@"距仲夏 7 周，第 6 天"]);
 assert(!zh::matchTemplate(@"Day 6 of 7th week before midsummer point",@"paragraph"));
 assert(!zh::matchTemplate(@"Day six of 7th week before midsummer point",@"showtext"));
 assert(!zh::matchTemplate(@"Day 6 of 7th week before midsummer point extra",@"showtext"));
 NSString* longtext=@"这是一段用于检验换行与完整性的中文长文。数字 123 和英文快捷键 ESC 应保持不变。";
 auto p=zh::layoutParagraph(longtext,70,{255,255,255,255});
 assert(p.height>12);NSMutableString* recovered=[NSMutableString new];
 for(auto& run:p.runs){assert(run.w<=70);[recovered appendString:run.text];}
 assert([recovered isEqual:longtext]);
 auto colored=zh::layoutParagraph(@"<red>红色</red><br>白色",70,{255,255,255,255});
 assert(colored.height==24);assert(colored.runs[0].color.r==168);assert(colored.runs.back().color.g==255);
 puts("runtime matching, wrapping, full-text preservation and color checks passed");
}}

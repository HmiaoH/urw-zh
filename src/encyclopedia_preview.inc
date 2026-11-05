// GameInfo_Hotspot truncates an English introduction before showtext.
// Retain the immutable topic ID for F1 and translate only the preview draws.
thread_local std::string previewTopic;
thread_local bool previewHasCustomText=false;
NSString* previewTranslation(int x,int y){
 if(previewTopic.empty()||x!=15||(y!=552&&y!=563))return nil;
 if(y==563&&previewHasCustomText)return nil;
 return translate(previewTopic.c_str(),y==552?"encyclopedia-title":"encyclopedia-summary");
}
void gameInfoPreview(char* topic,char* custom,int mode){@autoreleasepool{
 std::string previous=previewTopic;bool previousCustom=previewHasCustomText;
 previewTopic=[[[NSString alloc] initWithBytes:topic length:strlen(topic) encoding:CFStringConvertEncodingToNSStringEncoding(kCFStringEncodingDOSLatinUS)] uppercaseString].UTF8String;previewHasCustomText=custom&&*custom;
 original<void(*)(char*,char*,int)>("game_info_preview")(topic,custom,mode);
 previewTopic=previous;previewHasCustomText=previousCustom;
}}
void textureInfoPreview(SDL_Texture* target,char* topic,char* custom){@autoreleasepool{
 std::string previous=previewTopic;bool previousCustom=previewHasCustomText;
 previewTopic=[[[NSString alloc] initWithBytes:topic length:strlen(topic) encoding:CFStringConvertEncodingToNSStringEncoding(kCFStringEncodingDOSLatinUS)] uppercaseString].UTF8String;previewHasCustomText=custom&&*custom;
 original<void(*)(SDL_Texture*,char*,char*)>("texture_info_preview")(target,topic,custom);
 previewTopic=previous;previewHasCustomText=previousCustom;
}}

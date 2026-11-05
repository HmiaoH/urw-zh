// ProceedPause sends this button to the game's character-by-character painter.
bool drawCraftProceedButton(void(*fn)(int,int,char*),uintptr_t caller,int x,int y,char* text){
 constexpr uintptr_t returnAddress=0x10012c5e1ULL;
 constexpr char prompt[]=" [SPACE] to continue -- [ESC] cancel ";
 if(caller!=returnAddress||strcmp(text,prompt))return false;
 NSString* proceed=translate("to continue","craft-prompt");
 NSString* cancel=translate("cancel","craft-prompt");
 if(!proceed||!cancel)return false;
 // The native plate and key glyphs keep their original sizes and positions.
 constexpr int proceedColumn=9,cancelColumn=30,cell=8,textOffset=8;
 char display[sizeof(prompt)];
 memcpy(display,prompt,sizeof(prompt));
 memset(display+proceedColumn,' ',sizeof("to continue")-1);
 memset(display+cancelColumn,' ',sizeof("cancel")-1);
 fn(x,y,display);
 if(!drawSurface(x+textOffset+proceedColumn*cell,y+5,proceed,0,(sizeof("to continue")-1)*cell)||
    !drawSurface(x+textOffset+cancelColumn*cell,y+5,cancel,0,(sizeof("cancel")-1)*cell))
  fn(x,y,text);
 return true;
}

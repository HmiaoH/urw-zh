#!/usr/bin/env python3
"""Generate exact-build, relocation-free entry bindings; never scans unknown builds at runtime."""
import hashlib,json,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GAME=Path('/Users/chenjiahao/Library/Application Support/Steam/steamapps/common/UnRealWorld/UrW.app')
SUPPORTED_SHA256='124f89da263b7dabb323fd4f94718261abbe0ef76371a7e5ed5d6b50492ae112'
HOOKS={
'choose_culture':'__Z14choose_culturev',
'game_info_preview':'__Z16GameInfo_HotspotPcS_i',
'texture_info_preview':'__Z22toTex_GameInfo_HotspotP11SDL_TexturePcS1_',
'status_text_box':'__Z7TextBoxiiiPci',
'flip_screen_portion':'__Z17FlipScreenPortioniiiii',
'message_log':'__Z6MsgLogv', 'message_log_words':'__Z18SANATAULUKKO_LisaaiPc',
'armor_button':'__Z14Piirra_NappainiiPc',
'centered_text':'__Z7centextiiiPcji',
'hyper_show':'__Z9link_showPcS_', 'npc_talk':'__Z6CrTalkPc','player_talk':'__Z7PlrTalkPc',
'inventory_entry':'__Z20LIST_ButtonSpotEntryiiiPc',
'list_draw':'__Z9LIST_Drawv',
'held_item_bar':'__Z12TekstiPalkkiiiiPci',
'note':'__Z4NotePc',
'note_bottom':'__Z11note_bottomv',
'paragraph':'__Z21showtext_sanataulukkoiiiiji','renparagraph':'__Z19render_sanataulukkoP12SDL_Rendereriiii9SDL_Colori',
'show':'__Z8showtextiiPcji','text':'__Z7textputiiPc',
'renshow':'__Z11renshowtextP12SDL_RendereriiPc9SDL_Colorj',
'rentext':'__Z10rentextputP12SDL_RendereriiPc9SDL_Colorj',
'newtext':'__Z11New_rentextP12SDL_RendereriiPc9SDL_Colorj',
'newshow':'__Z11NewShowtextP11SDL_TextureiiPc9SDL_Colorj',
'asc':'__Z6putasciih','renasc':'__Z9renderascP12SDL_Rendereriihiiij',
'newasc':'__Z13New_renderascP12SDL_Rendereriihiiij'}
GLOBALS={'note':'_NOTE','notebox':'_noteboxGui','textlineh':'__Z9textlinehf','flipmap':'__Z11FlipWithMapv','words':'_SanaTaulukko','screen':'_screen','ren':'_ren','color':'_CURRENT_COLOR','x':'_scr_xpos','y':'_scr_ypos','convert':'__Z28NativeResolution_RectConvertP8SDL_Rect'}
GLOBALS.update({'hyper_x':'_HYPER_X','hyper_y':'_HYPER_Y','hyper_line':'_yie','link_pos':'_lpos','link_list':'_list','topics':'_topics','npc_x':'_CRTALKCOL','npc_y':'_CRTALKLINE','player_x':'_PLRTALKCOL','player_y':'_PLRTALKLINE','spot_entry':'__Z14LIST_SpotEntryiiiii','line':'__Z4lineiiii','flip':'__Z4Flipv'})
GLOBALS.update({'message_log_text':'_notebuf','message_log_format':'_formatbuf'})
GLOBALS.update({'heading_box':'_headingGui'})
GLOBALS.update({'screen_texture':'_tex'})
def inspect(path):
 b=path.read_bytes();assert b[:4]==b'\xcf\xfa\xed\xfe'
 n=struct.unpack_from('<I',b,16)[0];off=32;sections={};segments=[]
 for _ in range(n):
  cmd,size=struct.unpack_from('<II',b,off)
  if cmd==0x19:
   va,vs,fo,fs=struct.unpack_from('<QQQQ',b,off+24);segments.append((va,vs,fo,fs))
   ns=struct.unpack_from('<I',b,off+64)[0]
   for i in range(ns):
    p=off+72+i*80;name=b[p:p+16].split(b'\0')[0].decode();addr,sz,fp=struct.unpack_from('<QQI',b,p+32);sections[name]=(addr,sz,fp)
  off+=size
 syms={}
 for l in subprocess.check_output(['nm','-nm',str(path)],text=True).splitlines():
  if '(undefined)' not in l:
   parts=l.split()
   try:syms[parts[-1]]=int(parts[0],16)
   except (ValueError,IndexError):pass
 return b,segments,sections,syms
if __name__=='__main__':
 b,segs,secs,syms=inspect(GAME/'Contents/Resources/urw3-bin')
 if hashlib.sha256(b).hexdigest()!=SUPPORTED_SHA256:raise SystemExit('Unsupported binary: a new version requires manual disassembly and adaptation.')
 out={'version':'3.89.1','sha256':hashlib.sha256(b).hexdigest(),'hooks':{},'globals':{k:syms[v] for k,v in GLOBALS.items()},'global_symbols':GLOBALS}
 for key,sym in HOOKS.items():
  addr=syms[sym]; seg=next(s for s in segs if s[0]<=addr<s[0]+s[3]);p=addr-seg[0]+seg[2]
  # Common prologue through sub rsp; no relative instruction is relocated.
  if key=='list_draw':
   expected=bytes.fromhex('554889e541574156415541545350')
   # Include only push rax; total is 14 bytes and contains no RIP-relative operand.
   assert b[p:p+len(expected)]==expected
   out['hooks'][key]={'symbol':sym,'address':addr,'bytes':expected.hex()}
   continue
  if key=='note_bottom':
   expected=bytes.fromhex('554889e5415741564154534883ec20')
   assert b[p:p+len(expected)]==expected
   out['hooks'][key]={'symbol':sym,'address':addr,'bytes':expected.hex()}
   continue
  prefix=bytes.fromhex('554889e5415741564155415453')
  assert b[p:p+13]==prefix,(key,b[p:p+20].hex())
  length=17 if b[p+13:p+16]==bytes.fromhex('4883ec') else 20
  assert length==17 or b[p+13:p+16]==bytes.fromhex('4881ec')
  out['hooks'][key]={'symbol':sym,'address':addr,'bytes':b[p:p+length].hex()}
 (ROOT/'data/bindings.json').write_text(json.dumps(out,indent=2)+'\n')
 print(out['sha256'],len(out['hooks']),'hooks')

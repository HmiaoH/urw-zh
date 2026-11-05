import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from extract_sections import sections
from check_drafts import check,check_complete
from validate import validate

class CatalogTest(unittest.TestCase):
    def test_section_metadata_and_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'test'
            p.write_bytes('// comment\n.TOPIC.ALIAS.\nSome ä text<br>\n.LINK stays in body\n%POP%\nimage.jpg 400x300\n***'.encode('cp437'))
            rows=sections(p,'GAME.NFO')
        self.assertEqual(len(rows),1)
        r=rows[0]
        self.assertEqual(r['original'],'Some ä text<br> .LINK stays in body')
        self.assertEqual(r['metadata'],['%POP%','image.jpg 400x300'])
        self.assertEqual(r['aliases'],'.TOPIC.ALIAS.')
    def test_draft_source_integrity(self):
        r=dict(id='a',source='GAME.NFO',context='resource:a',original='5% to 25%<br>',translation='',status='pending')
        d=dict(r,translation='5%至25%<br>',status='draft')
        self.assertEqual(check([r],[d]),[])
        d['original']='changed'
        self.assertTrue(check([r],[d]))
    def test_lost_number(self):
        r=dict(id='a',source='GAME.NFO',context='resource:a',original='5 to 25',translation='',status='pending')
        self.assertTrue(check([r],[dict(r,translation='5至20',status='draft')]))
    def test_message_placeholder(self):
        r=dict(id='a',source='messages/urw_chat.txt',context='x',original='<plr_name> has %s',translation='',status='pending')
        self.assertTrue(check([r],[dict(r,translation='某人有%s',status='draft')]))

    def test_incomplete_queue(self):
        r=dict(id='a',source='GAME.NFO',original='Text')
        self.assertTrue(check_complete([r],[]))
        self.assertTrue(check_complete([r],[dict(r,exclusion_reason='skip')]))
        self.assertEqual(check_complete([r],[dict(r,translation='正文')]),[])

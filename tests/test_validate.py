import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from validate import validate

class ValidationTest(unittest.TestCase):
    def row(self, **kw):
        return dict(id='test',source='test',context='showtext',original='Day {day:int}',translation='第 {day} 天',status='reviewed',kind='template',**kw)
    def test_reordering(self):
        r=self.row(); r.update(original='{n:int} items for {who:text}',translation='{who}的 {n} 件物品')
        self.assertEqual(validate([r]),[])
    def test_missing_parameter(self):
        r=self.row();r['translation']='一天';self.assertTrue(validate([r]))
    def test_duplicate(self):
        self.assertTrue(validate([self.row(), self.row()]))
    def test_tags(self):
        r=self.row();r.update(original='<red>Day {day:int}</red>');self.assertTrue(validate([r]))
    def test_scope(self):
        r=self.row();r['context']='*';self.assertTrue(validate([r]))
    def test_printf(self):
        r=self.row();r.update(kind='exact',original='%d items',translation='%s 件物品');self.assertTrue(validate([r]))

    def test_printf_ordinal_suffix(self):
        r=dict(id='ordinal',source='binary',context='showtext',original='%dth day',translation='一天',status='draft')
        self.assertTrue(validate([r]))
    def test_identical_normalized_alias(self):
        r=dict(id='first',source='binary',context='showtext',original='Day ',translation='日期 ',status='draft')
        self.assertEqual(validate([r,dict(r,id='second',original='Day',translation='日期')]),[])
        self.assertTrue(validate([r,dict(r,id='second',translation='天')]))

    def test_segment_boundaries_and_content(self):
        r=dict(id='columns',source='test',context='showtext',original='STATE   VALUE',translation='状态数值',status='reviewed',segments=[dict(offset=0,width=32,text='状态'),dict(offset=64,width=40,text='数值')])
        self.assertEqual(validate([r]),[])
        r['segments'][1]['offset']=16
        self.assertTrue(validate([r]))
        r['segments'][1]['offset']=64
        r['segments'][1]['text']=''
        self.assertTrue(validate([r]))

if __name__=='__main__': unittest.main()

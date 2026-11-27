import sys, tempfile, unittest, json
from pathlib import Path
from unittest.mock import patch
from PIL import Image, ImageDraw
import numpy as np
root=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(root/"phan_mem"),str(root/"cong_cu")]
import chuyen_dong as m
from ve_chuyen_dong import split_sheet

class MotionTests(unittest.TestCase):
    def test_sheet(self):
        im=Image.new("RGB",(800,400),"white")
        d=ImageDraw.Draw(im)
        for r in range(2):
            for c in range(4):
                d.rectangle((c*200+65,r*200+20,c*200+125,r*200+178),fill="blue")
        fs=split_sheet(im,2,4)
        self.assertEqual(len(fs),8)
        self.assertEqual(len({f.size for f in fs}),1)
        self.assertEqual(fs[0].getpixel((0,0))[3],0)
    def test_reject_empty(self):
        with self.assertRaises(ValueError): split_sheet(Image.new("RGB",(800,400),"white"),2,4)
    def test_fallback(self):
        with patch.object(m,"frames",return_value=[]):
            self.assertEqual(m.frame_di("Hiền",["a","b"],"phải","trái",.3,.27),("b",True))
    def test_walk_pack(self):
        with patch.object(m,"frames",return_value=list("abcdefgh")),patch.object(m,"pack",return_value={"walk":{"direction":"phải"}}):
            self.assertEqual(len({m.frame_di("Hiền",["x"],"trái","phải",i*.0675+.001,.27)[0] for i in range(8)}),8)
    def test_mouth(self):
        levels=m.muc_mieng(np.r_[np.zeros(8),np.ones(8)*.3,np.ones(8)])
        self.assertEqual(set(levels.tolist()),{0,1,2})
    def test_idle_pose_guard(self):
        with patch.object(m,"frames",return_value=["a","b","c","d"]),patch.object(m,"pack",return_value={"idle":{"pose":"base"}}):
            self.assertEqual(m.frame_dung("Hiền","phone","original",1,2,True),"original")
            self.assertEqual(m.frame_dung("Hiền","base","original",1,2,True),"d")

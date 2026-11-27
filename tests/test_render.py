import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "phan_mem"))
import lam_phim as p

class RenderTests(unittest.TestCase):
    def doc(self, s):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "test.txt"
            f.write_text(s, encoding="utf-8")
            return p.doc_kich_ban(f)

    def test_parser(self):
        ds = self.doc("[Cảnh: pho_dem | Hiền 28]\n* Máy quay: tiến\nHiền (cận): Xin chào.\n")
        self.assertEqual(ds[0]["nv"], [("Hiền", 0.28)])
        self.assertEqual(ds[0]["loi"][0]["dong_tac"], [("Máy quay", "tiến")])

    def test_parser_rejects_bad_input(self):
        for s in ("", "Lời không có cảnh", "[Cảnh: pho_dem]\nsai cú pháp"):
            with self.subTest(s=s), self.assertRaises(ValueError):
                self.doc(s)

    def test_preview_without_tts(self):
        self.assertFalse(p.tao_giong([], None, preview=True))

    def test_wav(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "voice.wav"
            self.assertFalse(p.wav_hop_le(f))
            with wave.open(str(f), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
                w.writeframes(b"\x00\x01" * 160)
            self.assertTrue(p.wav_hop_le(f))
            f.write_bytes(b"bad")
            self.assertFalse(p.wav_hop_le(f))

    def test_invalid_camera(self):
        ds = self.doc("[Cảnh: pho_dem | Hiền 28]\n* Máy quay: sai\nHiền: Chào.\n")
        with patch.object(p, "lay_canh"), self.assertRaises(SystemExit):
            p.kiem_tra(ds)

    def test_formats(self):
        self.assertEqual(p.CHE_DO["1080p"], (1920, 1080, 25))
        self.assertEqual(p.CHE_DO["nhanh"], (640, 360, 15))

if __name__ == "__main__":
    unittest.main()

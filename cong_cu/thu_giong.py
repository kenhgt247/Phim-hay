# -*- coding: utf-8 -*-
"""Đọc thử một câu bằng tất cả giọng mẫu của VieNeu, lưu thành mp3 trong giong_mau/ để nghe và chọn."""
import os, subprocess, re
from vieneu import Vieneu

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RA = os.path.join(GOC, "giong_mau"); os.makedirs(RA, exist_ok=True)
CAU = "Ở cái phường nhỏ này, ai cũng biết anh Hiền. Nhưng không ai biết, người đàn ông hiền lành ấy lại là đại ca giang hồ."

tts = Vieneu()
ds = tts.list_preset_voices()
dong = ["# Các giọng mẫu của VieNeu. Nghe file mp3 cùng số thứ tự để chọn.", ""]
for i, muc in enumerate(ds, 1):
    nhan, ma = (muc if isinstance(muc, (list, tuple)) else (str(muc), muc))
    print(f"{i}. {nhan}  ({ma})", flush=True)
    try:
        audio = tts.infer(CAU, voice=ma)
    except Exception:
        audio = tts.infer(CAU, voice=nhan)
    wav = os.path.join(RA, "tam.wav"); tts.save(audio, wav)
    ten = re.sub(r"[^0-9A-Za-z]+", "_", str(ma)).strip("_") or f"giong{i}"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "96k", os.path.join(RA, f"{i:02d}_{ten}.mp3")], check=True)
    os.remove(wav)
    dong.append(f"{i:02d}. {nhan}    (mã: {ma})")
open(os.path.join(RA, "danh_sach_giong.txt"), "w", encoding="utf-8").write("\n".join(dong) + "\n")
print("Xong", len(ds), "giọng")

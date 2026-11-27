# -*- coding: utf-8 -*-
"""Tạo SO_TAY_BIEN_KICH.md: sổ tay cho ChatGPT/Gemini viết kịch bản đúng cách viết và chỉ dùng hình có trong kho.
Tự chạy lại sau mỗi lần vẽ kho hình."""
import os, re, sys, json
GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(GOC, "cong_cu")); sys.path.insert(0, os.path.join(GOC, "phan_mem"))
from ve_kho import doc_danh_sach

TACH = os.path.join(GOC, "kho", "tach")
TEN_NV = {"hien": "Hiền", "kela": "Kẻ lạ", "lan": "Lan", "bo": "Bố", "me": "Mẹ", "danem": "Đàn em", "tung": "Tùng"}
CO_SAN = {  # tư thế đặt tên sẵn trong phần mềm: (mô tả, nói được?)
    "Hiền": [("hiền", "đứng chính diện, tay cầm điện thoại, mặt hiền", True), ("lạnh", "đứng chính diện, cầm điện thoại, mặt lạnh", True),
             ("nghe", "áp điện thoại lên tai, mặt hiền", True), ("nghe lạnh", "áp điện thoại lên tai, mặt lạnh", True),
             ("túi", "thò tay vào túi quần (sắp rút điện thoại)", False), ("ngồi", "ngồi ghế làm việc nghiêng 3/4 sang phải", False),
             ("ngồi lạnh", "ngồi ghế nghiêng 3/4, mặt lạnh", False), ("mặt lạnh", "CẬN khuôn mặt lạnh", False),
             ("mặt giận", "CẬN khuôn mặt giận", False), ("mặt hiền", "CẬN khuôn mặt cười hiền", False)],
    "Kẻ lạ": [("đứng", "đứng nghiêng 3/4 sang trái, tay đút túi, cười nhếch mép", True), ("thường", "đứng chính diện tay đút túi", True),
              ("mặt cười", "CẬN khuôn mặt cười nhếch mép", False)],
}
BOI_CANH = {"pho_dem": "phố đêm dài có trung tâm Du Học Bình Minh, vỉa hè, đèn đường (nhân vật đi dọc phố được, vị trí 20-70)",
            "van_phong": "văn phòng trung tâm du học buổi sáng: bàn làm việc bên trái (Hiền ngồi ở vị trí 23), cửa kính bên phải (người lạ đi vào từ 112 tới 74)"}

def mo_ta_kho():
    ds = {}
    for h in doc_danh_sach():
        m = re.search(r"(?:Tư thế|Biểu cảm): (.*)$", h["lenh"])
        if m: ds[h["ten"]] = ("CẬN khuôn mặt: " if "Biểu cảm" in h["lenh"] else "") + m.group(1).strip()
        elif h["ten"].endswith("_tao"): ds[h["ten"]] = "đứng chính diện (dáng mặc định)"
        elif h["loai"] == "nền": ds[h["ten"]] = h["lenh"].split("Cảnh:")[-1].strip() if "Cảnh:" in h["lenh"] else h["lenh"][:120]
    return ds

def main():
    mo_ta = mo_ta_kho()
    co_hinh = {f[:-4] for f in os.listdir(TACH) if f.endswith(".png")}
    out = []
    out.append(open(os.path.join(GOC, "phan_mem", "cot_truyen.md"), encoding="utf-8").read().strip())
    out.append("""
## CÁCH VIẾT KỊCH BẢN (bắt buộc đúng từng ký tự)

```
[Cảnh: tên_bối_cảnh | Nhân vật vị trí, Nhân vật vị trí]
* Nhạc: bí ẩn            (bí ẩn / căng thẳng / ấm áp / buồn / tắt)
* Hiệu ứng: chớp         (rung / chớp / mưa / tắt mưa)
* Tên nhân vật: tư thế   (đổi tư thế, bắt đầu cùng câu thoại ngay sau)
* Tên nhân vật: đi tới 60
* Tên nhân vật: rung     (điện thoại trong túi rung)
* Máy quay: xa           (kéo máy quay ra sau một câu cận)
Dẫn chuyện: lời kể
Tên nhân vật: lời thoại
Tên nhân vật (cận): lời thoại, máy quay đẩy sát người nói
Tên nhân vật: …          (im lặng 1,6 giây, dùng cho cảnh nhìn nhau)
```

Quy tắc:
- Vị trí từ 0 (mép trái) đến 100 (mép phải). Trên 100 là đứng ngoài khung (để đi vào). Hai người đứng cách nhau ít nhất 30.
- Mọi nhân vật nói trong cảnh phải có tên trong dòng `[Cảnh: ...]`, trừ "Dẫn chuyện" và người nói qua điện thoại (viết `Đàn em (điện thoại): ...` mà không cần có mặt).
- Dòng `* ...` luôn đặt NGAY TRƯỚC câu thoại mà động tác bắt đầu.
- Khi nhân vật NÓI, phải đang ở **tư thế nói được** (danh sách bên dưới, đánh dấu 🗣). Muốn dùng tư thế khác thì cho nhân vật im lặng hoặc để Dẫn chuyện nói, rồi đổi lại tư thế nói được trước câu thoại.
- Cảnh CẬN khuôn mặt (tư thế có chữ "CẬN") chỉ dùng cho lúc im lặng hoặc khi Dẫn chuyện đang kể, không dùng khi nhân vật đó đang nói.
- Sau mỗi câu `(cận)` nên có `* Máy quay: xa`.
- Chỉ dùng ĐÚNG tên bối cảnh và tên tư thế trong danh sách. Không tự đặt tên mới.
- Mỗi câu thoại ngắn, tối đa khoảng 25 chữ. Câu dài thì tách làm hai dòng.
- Độ dài 3 phút: khoảng 650–750 chữ lời nói, 5–6 cảnh, 45–60 dòng lời.
- Trả lời bằng MỘT khối code chứa toàn bộ kịch bản, dòng đầu là `# TẬP n – TÊN TẬP`.
""")
    out.append("## BỐI CẢNH CÓ SẴN (dùng đúng tên)\n")
    for k, v in BOI_CANH.items(): out.append(f"- `{k}`: {v}")
    for ten, v in sorted(mo_ta.items()):
        if ten.startswith("nen_") and ten[4:] not in BOI_CANH and not ten.startswith("nen_van_phong") and os.path.exists(os.path.join(GOC, "kho", "goc", ten + ".png")):
            out.append(f"- `{ten[4:]}`: {v}")
    out.append("\n## NHÂN VẬT VÀ TƯ THẾ CÓ SẴN\n🗣 = tư thế nói được (miệng mấp máy). Không có 🗣 = chỉ để diễn, không nói.\n")
    nhom = {}
    for ten in sorted(co_hinh):
        if ten.endswith("_mo"): continue
        nhom.setdefault(ten.split("_")[0], []).append(ten)
    for ma, ten_nv in TEN_NV.items():
        out.append(f"\n### {ten_nv}")
        for (k, mt, noi) in CO_SAN.get(ten_nv, []):
            out.append(f"- {'🗣 ' if noi else ''}`{k}`: {mt}")
        for t in nhom.get(ma, []):
            noi = (t + "_mo") in co_hinh
            out.append(f"- {'🗣 ' if noi else ''}`{t}`: {mo_ta.get(t, '')}")
        if ten_nv not in CO_SAN: out.append(f"- (dáng mặc định khi vào cảnh: `{ma}_tao`)")
    out.append("\n## VÍ DỤ: KỊCH BẢN TẬP 2\n```\n" + open(os.path.join(GOC, "phan_mem", "kich_ban_tap2.txt"), encoding="utf-8").read().strip() + "\n```\n")
    open(os.path.join(GOC, "SO_TAY_BIEN_KICH.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("Đã tạo SO_TAY_BIEN_KICH.md")

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Tách bảng tư thế trong kho/goc/ thành từng hình riêng (nền trong suốt) vào kho/tach/.
Hình loại 'đơn' được xóa nền, loại 'nền' giữ nguyên. Tạo thêm kho/xem_truoc.png để xem nhanh cả kho."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(GOC, "cong_cu"))
from ve_kho import doc_danh_sach

KHO_GOC = os.path.join(GOC, "kho", "goc"); TACH = os.path.join(GOC, "kho", "tach")
os.makedirs(TACH, exist_ok=True)

def mat_na_nen(a):
    trang = (a.min(2) > 228) & ((a.max(2) - a.min(2)) < 22)
    nhan, _ = ndimage.label(trang)
    mep = set(np.unique(np.concatenate([nhan[0], nhan[-1], nhan[:, 0], nhan[:, -1]]))) - {0}
    return np.isin(nhan, list(mep))

def xoa_nen(im):
    a = np.asarray(im.convert("RGB")).astype(np.int16)
    alpha = ndimage.gaussian_filter((~mat_na_nen(a)).astype(np.float32), 0.8)
    out = Image.fromarray(np.dstack([a.astype(np.uint8), (alpha * 255).clip(0, 255).astype(np.uint8)]), "RGBA")
    return out

def tach(im):
    a = np.asarray(im.convert("RGB")).astype(np.int16)
    vat = ~mat_na_nen(a)
    gop = ndimage.binary_dilation(vat, iterations=max(6, im.width // 150))   # nối các phần của cùng một người
    nhan, n = ndimage.label(gop)
    hop = ndimage.find_objects(nhan)
    dt = ndimage.sum(vat, nhan, range(1, n + 1))
    lon = max(dt) if len(dt) else 0
    cac = [(hop[i], i + 1) for i in range(n) if dt[i] > lon * 0.15]
    # xếp theo hàng rồi theo cột
    cac.sort(key=lambda c: (c[0][0].start + c[0][0].stop) / 2)
    hang, cur, cao_tb = [], [], np.mean([c[0][0].stop - c[0][0].start for c in cac]) if cac else 1
    for c in cac:
        if cur and (c[0][0].start + c[0][0].stop) / 2 - (cur[0][0][0].start + cur[0][0][0].stop) / 2 > cao_tb * 0.5:
            hang.append(cur); cur = []
        cur.append(c)
    if cur: hang.append(cur)
    rgba = xoa_nen(im); ket = []
    for h in hang:
        for (sl, k) in sorted(h, key=lambda c: c[0][1].start):
            m = (nhan[sl] == k)
            phan = np.asarray(rgba)[sl].copy(); phan[..., 3] = (phan[..., 3] * m).astype(np.uint8)
            ket.append(Image.fromarray(phan, "RGBA"))
    return ket

def main():
    ds = {h["ten"]: h for h in doc_danh_sach()}
    for f in sorted(os.listdir(KHO_GOC)):
        if not f.endswith(".png"): continue
        ten = f[:-4]; loai = ds.get(ten, {}).get("loai", "đơn"); src = os.path.join(KHO_GOC, f)
        if loai == "nền": continue
        dau = os.path.join(TACH, ten + ("_1.png" if loai == "bảng" else ".png"))
        if os.path.exists(dau) and os.path.getmtime(dau) >= os.path.getmtime(src): continue
        for cu in os.listdir(TACH):
            if cu == ten + ".png" or (cu.startswith(ten + "_") and cu[len(ten) + 1:-4].isdigit()): os.remove(os.path.join(TACH, cu))
        im = Image.open(src)
        if loai == "bảng":
            ket = tach(im)
            for i, h in enumerate(ket, 1): h.save(os.path.join(TACH, f"{ten}_{i}.png"))
            print(f"- {ten}: tách được {len(ket)} hình" + ("  (KHÁC 6 - nên kiểm tra)" if len(ket) != 6 else ""))
        else:
            r = xoa_nen(im); r.crop(r.getbbox()).save(dau); print(f"- {ten}: đã xóa nền")
    # ảnh xem trước cả kho
    hinh = sorted(os.listdir(TACH))
    if hinh:
        o = 220; cot = 8; W = Image.new("RGB", (cot * o, ((len(hinh) + cot - 1) // cot) * (o + 24)), (235, 235, 235)); d = ImageDraw.Draw(W)
        for i, f in enumerate(hinh):
            t = Image.open(os.path.join(TACH, f)); t.thumbnail((o - 10, o - 10))
            x, y = (i % cot) * o, (i // cot) * (o + 24)
            W.paste(t, (x + (o - t.width) // 2, y + (o - t.height) // 2), t); d.text((x + 6, y + o + 4), f[:-4], fill=(0, 0, 0))
        W.save(os.path.join(GOC, "kho", "xem_truoc.png"))

if __name__ == "__main__":
    main()

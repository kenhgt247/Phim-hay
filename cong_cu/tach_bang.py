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

def tach(im, hang=2, cot=3):
    """Chia bảng thành lưới 2 hàng x 3 cột, mỗi ô lấy phần nhân vật lớn nhất, xóa nền."""
    rgba = xoa_nen(im); a = np.asarray(rgba); ket = []
    H, W = a.shape[:2]
    for r in range(hang):
        for c in range(cot):
            o = a[r * H // hang:(r + 1) * H // hang, c * W // cot:(c + 1) * W // cot].copy()
            vat = o[..., 3] > 40
            if vat.sum() < o.shape[0] * o.shape[1] * 0.01: continue
            nhan, n = ndimage.label(ndimage.binary_dilation(vat, iterations=4))
            if n > 1:
                dt = ndimage.sum(vat, nhan, range(1, n + 1)); giu = np.isin(nhan, [i + 1 for i in range(n) if dt[i] > dt.max() * 0.08])
                o[..., 3] = (o[..., 3] * giu).astype(np.uint8)
            h = Image.fromarray(o, "RGBA"); bb = h.getbbox()
            if bb: ket.append(h.crop(bb))
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
    hinh = sorted(f for f in os.listdir(TACH) if f.endswith(".png"))
    if hinh:
        o = 220; cot = 8; W = Image.new("RGB", (cot * o, ((len(hinh) + cot - 1) // cot) * (o + 24)), (235, 235, 235)); d = ImageDraw.Draw(W)
        for i, f in enumerate(hinh):
            t = Image.open(os.path.join(TACH, f)); t.thumbnail((o - 10, o - 10))
            x, y = (i % cot) * o, (i // cot) * (o + 24)
            W.paste(t, (x + (o - t.width) // 2, y + (o - t.height) // 2), t); d.text((x + 6, y + o + 4), f[:-4], fill=(0, 0, 0))
        W.save(os.path.join(GOC, "kho", "xem_truoc.png"))

if __name__ == "__main__":
    main()

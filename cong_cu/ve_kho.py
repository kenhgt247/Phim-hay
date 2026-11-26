# -*- coding: utf-8 -*-
"""Đọc danh_sach_hinh.txt, gọi Gemini API vẽ từng hình còn thiếu, lưu vào kho/goc/, rồi tách bảng tư thế.
Biến môi trường: GEMINI_API_KEY (bắt buộc), MODEL, VE_LAI (tên cách nhau dấu phẩy), CHI_VE (chỉ vẽ những tên này), GIOI_HAN (số hình tối đa mỗi lần)
"""
import os, re, sys, json, base64, time, io
import requests
from PIL import Image

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KHO_GOC = os.path.join(GOC, "kho", "goc")
MAU = os.path.join(GOC, "mau")
os.makedirs(KHO_GOC, exist_ok=True)

MODEL = os.environ.get("MODEL") or "gemini-nano-banana-2.1"
KHOA = os.environ.get("GEMINI_API_KEY", "").strip()

PHONG_CACH = "phong cách hoạt hình 2D kiểu truyện tranh động Trung Quốc, nét viền đậm, màu phẳng, đẹp, chất lượng cao"
GIU_MAT = "Vẽ đúng nhân vật trong ảnh mẫu (giữ nguyên khuôn mặt, kiểu tóc, quần áo, màu sắc và nét vẽ), " + PHONG_CACH + ". "
LENH_TU_THE = GIU_MAT + ("Chỉ vẽ MỘT nhân vật duy nhất, toàn thân từ đầu đến chân, đứng giữa khung hình, chừa khoảng trắng xung quanh, "
                         "không bị cắt mép, nền trắng trơn hoàn toàn, không chữ, không bóng đổ, miệng ngậm. Tư thế: ")
LENH_MAT = GIU_MAT + ("Chỉ vẽ khuôn mặt cận cảnh từ vai trở lên, ở giữa khung hình, nền trắng trơn hoàn toàn, không chữ, miệng ngậm. Biểu cảm: ")
MACRO = {
    "{TAO}": ("Vẽ một nhân vật " + PHONG_CACH + ". Chỉ một người, toàn thân từ đầu đến chân, đứng chính diện, miệng ngậm, "
              "nền trắng trơn hoàn toàn, không chữ, không bị cắt mép. Nhân vật:"),
    "{NEN}": ("Vẽ bối cảnh " + PHONG_CACH + ", khung 16:9, không có người, chữ trên biển hiệu viết đúng chính tả tiếng Việt. Cảnh:"),
    "{BANG_CHUNG}": ("1. Đứng nghiêng 3/4 sang phải  2. Đứng nghiêng 3/4 sang trái  3. Đi bộ nhìn nghiêng sang phải, chân trái bước trước  "
                     "4. Đi bộ nhìn nghiêng sang phải, hai chân gần khép  5. Ngồi ghế nghiêng 3/4 sang phải  6. Đứng nói chuyện điện thoại"),
}

def doc_danh_sach():
    """Trả về danh sách VIỆC VẼ. Mỗi mục 'bảng' được tách thành từng tư thế: ten_1, ten_2, ..."""
    muc, cur = [], None
    for dong in open(os.path.join(GOC, "danh_sach_hinh.txt"), encoding="utf-8"):
        s = dong.strip()
        if s.startswith("## "):
            phan = [p.strip() for p in s[3:].split("|")]
            cur = {"ten": phan[0], "mau": "", "loai": "đơn", "lenh": ""}
            for p in phan[1:]:
                if ":" in p:
                    k, val = [x.strip() for x in p.split(":", 1)]
                    if k == "mẫu": cur["mau"] = val
                    if k == "loại": cur["loai"] = val
            muc.append(cur); continue
        if not s or s.startswith("#") or cur is None: continue
        cur["lenh"] += " " + s
    viec = []
    for h in muc:
        l = h["lenh"]
        for k, val in MACRO.items(): l = l.replace(k, val)
        if h["loai"] == "bảng":
            mat = "{MAT}" in l
            l = l.replace("{BANG}", "").replace("{MAT}", "")
            cac = [x.strip() for x in re.split(r"(?:^|\s)\d+\.\s", " " + l) if x.strip()]
            for i, tt in enumerate(cac, 1):
                viec.append({"ten": f"{h['ten']}_{i}", "nhom": h["ten"], "mau": h["mau"], "loai": "mặt" if mat else "tư thế",
                             "lenh": (LENH_MAT if mat else LENH_TU_THE) + tt})
        else:
            viec.append({"ten": h["ten"], "nhom": h["ten"], "mau": h["mau"], "loai": h["loai"], "lenh": l.strip()})
    return viec

def tim_mau(ten):
    for thu_muc in (MAU, KHO_GOC):
        for duoi in (".png", ".jpg", ".jpeg"):
            p = os.path.join(thu_muc, ten + duoi)
            if os.path.exists(p): return p
    return None

def anh_b64(p):
    im = Image.open(p).convert("RGB"); im.thumbnail((1536, 1536))
    b = io.BytesIO(); im.save(b, "JPEG", quality=92); return base64.b64encode(b.getvalue()).decode()

def tim_anh(obj):
    """Tìm dữ liệu ảnh base64 ở bất kỳ đâu trong phản hồi."""
    if isinstance(obj, dict):
        mime = str(obj.get("mime_type") or obj.get("mimeType") or "")
        data = obj.get("data")
        if isinstance(data, str) and len(data) > 1000 and (mime.startswith("image") or not mime):
            return data
        for v in obj.values():
            r = tim_anh(v)
            if r: return r
    elif isinstance(obj, list):
        for v in obj:
            r = tim_anh(v)
            if r: return r
    return None

def goi_api(lenh, mau_path, khung, co):
    tieu_de = {"x-goog-api-key": KHOA, "Content-Type": "application/json"}
    # Cách mới: Interactions API
    vao = [{"type": "text", "text": lenh}]
    if mau_path: vao.append({"type": "image", "mime_type": "image/jpeg", "data": anh_b64(mau_path)})
    body = {"model": MODEL, "input": vao,
            "response_format": {"type": "image", "mime_type": "image/jpeg", "aspect_ratio": khung, "image_size": co}}
    r = requests.post("https://generativelanguage.googleapis.com/v1beta/interactions", headers=tieu_de, json=body, timeout=300)
    if r.ok:
        d = tim_anh(r.json())
        if d: print("  (dùng cách mới)"); return base64.b64decode(d)
    loi1 = f"{r.status_code} {r.text[:400]}"
    print(f"  (cách mới không được: {loi1[:300]}) -> thử cách cũ")
    # Cách cũ: generateContent (dự phòng)
    parts = [{"text": lenh}]
    if mau_path: parts.append({"inline_data": {"mime_type": "image/jpeg", "data": anh_b64(mau_path)}})
    body2 = {"contents": [{"parts": parts}],
             "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": khung, "imageSize": co}}}
    r2 = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent", headers=tieu_de, json=body2, timeout=300)
    if r2.ok:
        d = tim_anh(r2.json())
        if d: return base64.b64decode(d)
    raise RuntimeError(f"Không nhận được ảnh.\n  Cách mới: {loi1}\n  Cách cũ: {r2.status_code} {r2.text[:400]}")

def main():
    if not KHOA:
        print("THIẾU KHÓA: chưa thêm GEMINI_API_KEY vào Secrets của kho GitHub."); sys.exit(1)
    ve_lai = {x.strip() for x in os.environ.get("VE_LAI", "").split(",") if x.strip()}
    chi_ve = {x.strip() for x in os.environ.get("CHI_VE", "").split(",") if x.strip()}
    gioi_han = int(os.environ.get("GIOI_HAN") or 100)
    ds = doc_danh_sach(); da_ve, loi = 0, []
    for h in ds:
        ten = h["ten"]; ra = os.path.join(KHO_GOC, ten + ".png")
        if chi_ve and ten not in chi_ve and h["nhom"] not in chi_ve: continue
        if os.path.exists(ra) and ten not in ve_lai and h["nhom"] not in ve_lai: continue
        if da_ve >= gioi_han: break
        mau = None
        if h["mau"]:
            mau = tim_mau(h["mau"])
            if not mau: print(f"- Bỏ qua {ten}: chưa có ảnh mẫu '{h['mau']}' (vẽ hình đó trước)."); continue
        khung, co = {"nền": ("16:9", "2K"), "mặt": ("1:1", "1K")}.get(h["loai"], ("3:4", "1K"))
        print(f"- Đang vẽ {ten} ...", flush=True)
        for lan in range(3):
            try:
                du_lieu = goi_api(h["lenh"], mau, khung, co)
                Image.open(io.BytesIO(du_lieu)).convert("RGB").save(ra)
                print(f"  xong: kho/goc/{ten}.png"); da_ve += 1; break
            except Exception as e:
                print(f"  lỗi lần {lan + 1}: {e}")
                time.sleep(10)
        else:
            loi.append(ten)
    print(f"\nĐã vẽ {da_ve} hình." + (f" Lỗi: {', '.join(loi)}" if loi else ""))
    if loi and da_ve == 0: sys.exit(1)

if __name__ == "__main__":
    main()

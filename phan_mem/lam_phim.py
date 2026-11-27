# -*- coding: utf-8 -*-
"""
LÀM PHIM – xưởng phim hoạt hình đơn giản (bản 1.1)
Cách dùng:   python lam_phim.py kich_ban_tap1.txt
- Có VieNeu-TTS (pip install vieneu): giọng thật, miệng mấp máy theo giọng.
- Chưa có: ra bản XEM TRƯỚC không tiếng.
Cần: Python 3, Pillow, numpy, scipy, ffmpeg.
"""
import os, re, sys, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import am_thanh

THU_MUC = os.path.dirname(os.path.abspath(__file__))
ANH = os.path.join(os.path.dirname(THU_MUC), "mau")

# ====== CÀI ĐẶT ==============================================================
RONG, CAO, FPS = 1280, 720, 25

# tư thế -> (ảnh ngậm miệng, ảnh mở miệng hoặc None, [cỡ so với dáng đứng]).  "đi" -> [bước A, bước B]
# tư thế dạng {"mat": ảnh} = cảnh cận khuôn mặt (cắt sang cận mặt, nền mờ)
NHAN_VAT = {
    "Hiền": {
        "mac_dinh": "hiền", "huong_di": "phải",
        "hiền": ("hien_hien_ngam.png", "hien_hien_mo.png"),
        "lạnh": ("hien_lanh_ngam.png", "hien_lanh_mo.png"),
        "nghe": ("hien_nghe_ngam.png", "hien_nghe_mo.png"),
        "nghe lạnh": ("hien_nghelanh_ngam.png", "hien_nghelanh_mo.png"),
        "túi": ("hien_tui.png", None),
        "ngồi": ("hien_bang_ngoi_1.png", None, 0.80),
        "ngồi lạnh": ("hien_bang_lanh_5.png", None, 0.80),
        "mặt lạnh": {"mat": "hien_bang_mat_2.png"},
        "mặt giận": {"mat": "hien_bang_mat_3.png"},
        "mặt hiền": {"mat": "hien_bang_mat_1.png"},
        "đi": ["hien_di_a.png", "hien_di_b.png"],
    },
    "Kẻ lạ": {
        "mac_dinh": "đứng", "huong_di": "trái",
        "đứng": ("kela_bang_1.png", "kela_dung_mo.png"),
        "thường": ("kela_ngam.png", "kela_mo.png"),
        "mặt cười": {"mat": "kela_bang_mat_1.png"},
        "đi": ["kela_di_a.png", "kela_di_b.png"],
    },
}
# Bối cảnh: ảnh, chân (độ cao chân 0-1, hoặc danh sách (vị trí, độ cao chân, cỡ)), chiều cao người, khung máy quay, màu ánh sáng,
#           tien_canh = vùng đồ vật đứng TRƯỚC nhân vật (vd. cái bàn), toạ độ 0-1
BOI_CANH = {
    "pho_dem":    {"anh": "bg_pho_dem.png",
                   "chan": [(0, 0.80, 1.0), (0.3, 0.778, 1.0), (0.5, 0.748, 0.9), (0.7, 0.715, 0.75), (0.9, 0.685, 0.6), (1.0, 0.67, 0.55)], "cao_nv": 0.30, "khung": 0.56, "mau": (0.80, 0.74, 0.66), "am_nen": "pho_dem"},
    "van_phong":  {"anh": "nen_van_phong_trong.png",
                   "chan": [(0, 0.865, 1.0), (0.33, 0.865, 1.0), (0.6, 0.90, 1.0), (1.0, 0.95, 1.04)], "cao_nv": 0.50, "khung": 1.00, "mau": (1.00, 0.98, 0.95), "am_nen": "van_phong",
                   "tien_canh": [(0.115, 0.775), (0.20, 0.725), (0.40, 0.705), (0.625, 0.69), (0.625, 1.0), (0.115, 1.0)]},
}
# Giọng VieNeu cho từng vai (tên giọng có sẵn)
GIONG = {"Dẫn chuyện": "Thiện Minh", "Hiền": "Hải Đăng", "Hiền trẻ": "Hải Đăng", "Kẻ lạ": "Adam bựa", "Hắc": "Adam bựa",
         "Đàn em": "Quốc Tuấn", "Tuấn": "Quốc Tuấn", "Tùng": "Phạm Tuyên", "Lan": "Ngọc Huyền", "Bố": "Xuân Vĩnh",
         "Mẹ": "Đoan Trang", "Anh Tâm": "Thanh Bình", "Tâm": "Thanh Bình", "Thiếu tá Minh": "Minh Đức", "Minh": "Minh Đức",
         "Ngọc": "Trúc Ly", "Bống": "Quỳnh Anh", "Chủ xưởng": "Quang Sơn"}
THU_MUC_ANH = [ANH, os.path.join(os.path.dirname(THU_MUC), "kho", "tach"), os.path.join(THU_MUC, "anh_them"),
               os.path.join(os.path.dirname(THU_MUC), "kho", "goc")]
# =============================================================================

GIAY_MOI_TIENG, NGHI = 0.27, 0.6
TOC_DO_DI = 0.62      # chiều cao nhân vật / giây
NHIP_BUOC = 0.27      # giây mỗi hình bước

# Nhân vật khác trong kho: tên trong kịch bản -> tiền tố tên ảnh
MA_NV = {"Lan": "lan", "Bố": "bo", "Mẹ": "me", "Đàn em": "danem", "Tuấn": "danem", "Tùng": "tung",
         "Anh Tâm": "tam", "Tâm": "tam", "Thiếu tá Minh": "minh", "Minh": "minh", "Ngọc": "ngoc", "Hiền trẻ": "hientre"}
TEN_KHAC = {"Hắc": "Kẻ lạ"}   # tên gọi khác của nhân vật đã khai báo
CANH_DEM = {"bo_ke": (0.80, 0.78, 0.82), "quan_nhau": (0.92, 0.82, 0.70), "phong_kin": (0.85, 0.75, 0.62)}

def lay_nv(ten):
    if ten in TEN_KHAC: return lay_nv(TEN_KHAC[ten])
    if ten in NHAN_VAT: return NHAN_VAT[ten]
    p = MA_NV.get(ten)
    if not p: raise KeyError(f"Chưa có nhân vật '{ten}'. Có: {', '.join(list(NHAN_VAT) + list(MA_NV))}")
    NHAN_VAT[ten] = {"mac_dinh": "thường", "huong_di": "phải", "thường": (f"{p}_tao.png", None),
                     "đi": [f"{p}_bang_3.png", f"{p}_bang_4.png"]}
    return NHAN_VAT[ten]

_mo_ta = None
def mo_ta_tu_the():
    """Mô tả tư thế lấy từ danh_sach_hinh.txt (để biết tư thế nào là ngồi)."""
    global _mo_ta
    if _mo_ta is None:
        _mo_ta = {}
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(THU_MUC), "cong_cu")); from ve_kho import doc_danh_sach
            for h in doc_danh_sach():
                m = re.search(r"Tư thế: (.*)$", h["lenh"])
                if m: _mo_ta[h["ten"]] = m.group(1).strip()
        except Exception: pass
    return _mo_ta

def tu_the_cua(cf, ten_tt):
    """Tư thế theo tên đặt sẵn, hoặc theo tên ảnh trong kho (vd. hien_bang_lanh_3)."""
    if ten_tt in cf: return cf[ten_tt]
    ten_anh = ten_tt.replace(".png", "")
    tim_file(ten_anh + ".png")
    if "_mat_" in ten_anh: return {"mat": ten_anh + ".png"}
    mt = mo_ta_tu_the().get(ten_anh, "").lower()
    ngoi = "ngoi" in ten_anh or mt.startswith(("ngồi", "nằm")) or ten_anh in ("hien_bang_lanh_5", "kela_bang_5")
    return (ten_anh + ".png", None, 0.80 if ngoi else 1.0)

_mo = {}
def mo_cua(ngam):
    """Tự tìm ảnh mở miệng: <tên>_mo.png trong kho (nếu có)."""
    if ngam not in _mo:
        try: tim_file(ngam[:-4] + "_mo.png"); _mo[ngam] = ngam[:-4] + "_mo.png"
        except FileNotFoundError: _mo[ngam] = None
    return _mo[ngam]

def lay_canh(ten):
    if ten in BOI_CANH: return BOI_CANH[ten]
    ten_anh = ten if ten.startswith(("nen_", "bg_")) else "nen_" + ten
    tim_file(ten_anh + ".png"); k = ten_anh.replace("nen_", "")
    BOI_CANH[ten] = {"anh": ten_anh + ".png", "chan": 0.93, "cao_nv": 0.55, "khung": 1.0,
                     "mau": CANH_DEM.get(k, (1.0, 0.98, 0.95)), "am_nen": "pho_dem" if k in ("bo_ke", "quan_nhau") else None}
    return BOI_CANH[ten]

def theo_vi_tri(chan, x):
    """Trả về (độ cao chân, hệ số cỡ) tại vị trí x."""
    if not isinstance(chan, list): return chan, 1.0
    xs = [p[0] for p in chan]
    return float(np.interp(x, xs, [p[1] for p in chan])), float(np.interp(x, xs, [p[2] for p in chan]))

def tim_font(co):
    for p in ["C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        if os.path.exists(p): return ImageFont.truetype(p, co)
    return ImageFont.load_default()

def chu_phu_de(s): return re.sub(r"\[[^\]]*\]\s*", "", s).strip()
def im_lang(s): return not chu_phu_de(s).strip(". …")

# ---------------- đọc kịch bản ----------------
def doc_kich_ban(p):
    ds, canh, cho = [], None, []
    for dong in open(p, encoding="utf-8"):
        dong = dong.strip()
        if not dong or dong.startswith("#"): continue
        m = re.match(r"\[Cảnh:\s*([^|\]]+)\|?([^\]]*)\]", dong)
        if m:
            nv = []
            for ph in [x.strip() for x in m.group(2).split(",") if x.strip()]:
                mm = re.match(r"(.+?)\s+(-?\d+)$", ph)
                nv.append((mm.group(1), float(mm.group(2)) / 100) if mm else (ph, 0.5))
            canh = {"nen": m.group(1).strip(), "nv": nv, "loi": []}; ds.append(canh); continue
        m = re.match(r"\*\s*([^:]+):\s*(.*)", dong)
        if m:
            for dt in [x.strip() for x in m.group(2).split(",") if x.strip()]:
                cho.append((m.group(1).strip(), dt))
            continue
        m = re.match(r"([^:(]+?)\s*(?:\(([^)]*)\))?\s*:\s*(.*)", dong)
        if m and canh is not None:
            the = [t.strip() for t in (m.group(2) or "").split(",") if t.strip()]
            canh["loi"].append({"ai": m.group(1).strip(), "the": the, "noi": m.group(3).strip(), "dong_tac": cho}); cho = []
    return ds

# ---------------- giọng ----------------
def tao_giong(ds, tam):
    try:
        from vieneu import Vieneu; tts = Vieneu()
    except Exception:
        print(">> Chưa có VieNeu-TTS: làm bản xem trước không tiếng."); return False
    i = 0
    for c in ds:
        for l in c["loi"]:
            i += 1
            if im_lang(l["noi"]): continue
            text, ra, g = l["noi"].replace("…", "..."), os.path.join(tam, f"cau_{i:03d}.wav"), GIONG.get(l["ai"])
            audio = tts.infer(text, voice=g) if g else tts.infer(text)
            tts.save(audio, ra); l["wav"] = ra; print(f"   giọng {i}: {l['ai']}")
    return True

def doc_wav(p):
    with wave.open(p) as w:
        sr, n, ch, sw = w.getframerate(), w.getnframes(), w.getnchannels(), w.getsampwidth()
        d = np.frombuffer(w.readframes(n), dtype={2: np.int16, 4: np.int32}[sw]).astype(np.float32)
    if ch > 1: d = d.reshape(-1, ch).mean(1)
    return d / (np.abs(d).max() + 1e-9), sr

# ---------------- ảnh ----------------
def tim_file(f):
    for d in THU_MUC_ANH:
        p = os.path.join(d, f)
        if os.path.exists(p): return p
    raise FileNotFoundError(f"Không tìm thấy ảnh {f}")

_cache = {}
def tach_nen(f):
    if f in _cache: return _cache[f]
    path = tim_file(f); goc = Image.open(path)
    if goc.mode == "RGBA" and np.asarray(goc)[..., 3].min() < 10:
        _cache[f] = goc.crop(goc.getbbox()); return _cache[f]
    im = goc.convert("RGB"); a = np.asarray(im).astype(np.int16)
    trang = (a.min(2) > 232) & ((a.max(2) - a.min(2)) < 18)
    nhan, _ = ndimage.label(trang)
    mep = set(np.unique(np.concatenate([nhan[0], nhan[-1], nhan[:, 0], nhan[:, -1]]))) - {0}
    alpha = ndimage.gaussian_filter((~np.isin(nhan, list(mep))).astype(np.float32), 0.8)
    rgba = Image.fromarray(np.dstack([np.asarray(im), (alpha * 255).clip(0, 255).astype(np.uint8)]), "RGBA")
    _cache[f] = rgba.crop(rgba.getbbox()); return _cache[f]

_cache2 = {}
def hinh_nv(f, cao_px, mau, lat):
    k = (f, int(cao_px), mau, lat)
    if k in _cache2: return _cache2[k]
    h = tach_nen(f); ti_le = cao_px / h.height
    h = h.resize((max(1, int(h.width * ti_le)), max(1, int(h.height * ti_le))), Image.LANCZOS)
    a = np.asarray(h).astype(np.float32); a[..., :3] *= np.array(mau, np.float32)
    h = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
    if lat: h = h.transpose(Image.FLIP_LEFT_RIGHT)
    _cache2[k] = h; return h

import functools
@functools.lru_cache(None)
def bong(rong, cao):
    im = Image.new("RGBA", (rong * 2, cao * 4), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((rong / 2, cao * 1.5, rong * 1.5, cao * 2.5), fill=(0, 0, 0, 120))
    return im.filter(ImageFilter.GaussianBlur(cao * 0.45))

# ---------------- dựng ----------------
def kiem_tra(ds):
    """Kiểm tra kịch bản trước khi dựng: bối cảnh, nhân vật, tư thế phải có trong kho."""
    loi = []
    for i, c in enumerate(ds, 1):
        try: lay_canh(c["nen"])
        except Exception as e: loi.append(f"Cảnh {i}: không có bối cảnh '{c['nen']}'")
        co_mat = {t for t, _ in c["nv"]}
        for t, _ in c["nv"]:
            try: lay_nv(t)
            except Exception: loi.append(f"Cảnh {i}: không có nhân vật '{t}'")
        for l in c["loi"]:
            for ai, dt in l["dong_tac"]:
                if ai in ("Máy quay", "Nhạc", "Hiệu ứng"): continue
                if ai not in co_mat: loi.append(f"Cảnh {i}: '{ai}' có động tác nhưng chưa có trong dòng [Cảnh: ...]"); continue
                if dt.startswith("đi tới") or dt == "rung": continue
                try: tu_the_cua(lay_nv(ai), dt)
                except Exception: loi.append(f"Cảnh {i}: '{ai}' không có tư thế '{dt}'")
    if loi:
        print("\n❌ KỊCH BẢN CÓ LỖI, chưa dựng được:\n  - " + "\n  - ".join(loi)); sys.exit(1)

def lam_phim(kb):
    ds = doc_kich_ban(kb)
    kiem_tra(ds)
    tam = os.path.join(THU_MUC, "_tam"); os.makedirs(tam, exist_ok=True)
    co_tieng = tao_giong(ds, tam)
    H = int(CAO * 1.25)

    t = 0.0; nhac_sk, hu_sk = [], []
    for c in ds:
        bc = lay_canh(c["nen"])
        nen = Image.open(tim_file(bc["anh"])).convert("RGB")
        W = int(nen.width * H / nen.height)
        c["W"], c["bc"] = W, bc
        c["nen_img"] = nen.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.1))
        c["nen_mo"] = nen.resize((RONG, CAO), Image.LANCZOS).filter(ImageFilter.GaussianBlur(9))
        c["nen_mo"] = Image.blend(Image.new("RGB", (RONG, CAO)), c["nen_mo"], 0.55)
        c["tien_canh"] = None
        if bc.get("tien_canh"):
            mk = Image.new("L", (W, H), 0)
            ImageDraw.Draw(mk).polygon([(x * W, y * H) for x, y in bc["tien_canh"]], fill=255)
            tc_ = c["nen_img"].convert("RGBA"); tc_.putalpha(mk.filter(ImageFilter.GaussianBlur(1.5))); c["tien_canh"] = tc_
        cao_nv = bc["cao_nv"] * H
        c["cao_nv"] = cao_nv
        # trạng thái nhân vật theo thời gian
        nvs = {}
        for ten, x in c["nv"]:
            cf = lay_nv(ten)
            nvs[ten] = {"x": x, "tu_the": [(-1, cf["mac_dinh"])], "di": [], "rung": []}
        c["nvs"] = nvs; c["t0"] = t; c["can"] = []
        can = None
        for l in c["loi"]:
            l["t0"] = t
            for ai, dt in l["dong_tac"]:
                if ai == "Nhạc": nhac_sk.append((t, dt)); continue
                if ai == "Hiệu ứng": hu_sk.append((t, dt)); continue
                if ai == "Máy quay":
                    if dt == "xa": can = None; c["can"].append((t, None))
                    continue
                n = nvs[ai]
                m = re.match(r"đi tới\s*(-?\d+)", dt)
                if m:
                    x_moi = float(m.group(1)) / 100
                    x_cu = n["di"][-1][3] if n["di"] else n["x"]
                    dai = abs(x_moi - x_cu) * W / (TOC_DO_DI * cao_nv)
                    n["di"].append((t, t + dai, x_cu, x_moi))
                elif dt == "rung": n["rung"].append(t)
                else: n["tu_the"].append((t, dt))
            if "wav" in l:
                d, sr = doc_wav(l["wav"]); dai = len(d) / sr; cs = int(sr / FPS)
                rms = np.array([np.sqrt((d[i:i + cs] ** 2).mean() + 1e-12) for i in range(0, len(d), cs)])
                l["mieng"] = rms > max(0.05, rms.max() * 0.18)
            elif im_lang(l["noi"]): dai = 1.6
            else: dai = len(chu_phu_de(l["noi"]).split()) * GIAY_MOI_TIENG + 0.3
            l["t1"] = t + dai
            if "cận" in l["the"]: can = l["ai"]; c["can"].append((t, can))
            elif l["ai"] in nvs and can is not None: can = None; c["can"].append((t, None))
            t += dai + NGHI
        het_di = max([d_[1] for n in nvs.values() for d_ in n["di"]] + [0])
        t = max(t, het_di + 0.3)
        c["t1"] = t + 0.5; t += 0.5
    tong = t

    # ---------------- âm thanh: giọng + nhạc nền + tiếng môi trường + tiếng động ----------------
    wav_ra = os.path.join(tam, "tieng.wav"); sr = am_thanh.SR; N = int(tong * sr) + sr
    giong = np.zeros(N, np.float32); dong = np.zeros(N, np.float32); moi_truong = np.zeros(N, np.float32); nhac_bg = np.zeros(N, np.float32)
    def them(buf, x, t0, am=1.0):
        i = int(t0 * sr)
        if i >= N or i + len(x) <= 0: return
        x = x[max(0, -i):]; i = max(i, 0); m = min(len(x), N - i); buf[i:i + m] += x[:m] * am
    for c in ds:
        for l in c["loi"]:
            if "wav" in l:
                d, s0 = doc_wav(l["wav"])
                if s0 != sr: d = np.interp(np.linspace(0, len(d), int(len(d) * sr / s0), endpoint=False), np.arange(len(d)), d).astype(np.float32)
                them(giong, d, l["t0"], 0.9)
        if c["bc"].get("am_nen"):
            x = am_thanh.nen_moi_truong(c["bc"]["am_nen"], c["t1"] - c["t0"]) * am_thanh.bao(c["t1"] - c["t0"], 0.4, 0.4)
            them(moi_truong, x, c["t0"])
        for n in c["nvs"].values():
            for r in n["rung"]: them(dong, am_thanh.rung_dien_thoai(), r)
            for (a, b, x0, x1) in n["di"]:
                k = a
                while k < b: them(dong, am_thanh.buoc_chan(), k, 0.7); k += NHIP_BUOC
    # nhạc: mỗi lệnh "* Nhạc: ..." chạy đến lệnh nhạc kế tiếp
    for i, (t0, kieu) in enumerate(nhac_sk):
        t1 = nhac_sk[i + 1][0] if i + 1 < len(nhac_sk) else tong
        if kieu.strip() == "tắt" or t1 - t0 < 1: continue
        them(nhac_bg, am_thanh.nhac(kieu.strip(), t1 - t0 + 1.5), t0)
    # mưa: chỉ trong cảnh có lệnh mưa, hết cảnh thì tắt
    for c in ds:
        mua_tu = None
        for t0, kieu in [x for x in hu_sk if c["t0"] <= x[0] < c["t1"]] + [(c["t1"], "tắt mưa")]:
            if kieu == "mưa" and mua_tu is None: mua_tu = t0
            elif kieu == "tắt mưa" and mua_tu is not None and t0 - mua_tu > 0.5:
                them(moi_truong, am_thanh.nen_moi_truong("mua", t0 - mua_tu) * am_thanh.bao(t0 - mua_tu, 1, 1), mua_tu); mua_tu = None
    # nhạc nhỏ đi khi có người nói
    co_noi = np.abs(giong) > 0.02
    w = int(0.25 * sr); co_noi = np.convolve(co_noi.astype(np.float32), np.ones(w) / w, "same")
    tron = giong + dong * 0.9 + moi_truong * 0.35 + nhac_bg * (0.22 - 0.12 * np.clip(co_noi * 3, 0, 1))
    tron = np.tanh(tron * 1.1) * 0.9
    with wave.open(wav_ra, "w") as w_:
        w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(sr); w_.writeframes((tron * 32767).astype(np.int16).tobytes())

    ra = os.path.splitext(kb)[0] + ("" if co_tieng else "_xem_truoc") + ".mp4"
    lenh = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{RONG}x{CAO}", "-r", str(FPS), "-i", "-"]
    lenh += ["-i", wav_ra, "-c:a", "aac", "-b:a", "160k", "-shortest"]
    lenh += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", ra]
    ff = subprocess.Popen(lenh, stdin=subprocess.PIPE)
    font = tim_font(46)
    so_khung = int(tong * FPS); print(f">> Dựng {so_khung} khung hình ({tong:.0f} giây)...")
    cam = None; canh_truoc = None
    # hiệu ứng hình: tối viền, mưa, rung khung, chớp sáng
    yy, xx = np.mgrid[0:CAO, 0:RONG]; r_ = np.sqrt(((xx - RONG / 2) / (RONG / 2)) ** 2 + ((yy - CAO / 2) / (CAO / 2)) ** 2)
    toi_vien = Image.fromarray((np.clip((r_ - 0.75) / 0.7, 0, 1) * 150).astype(np.uint8), "L")
    den = Image.new("RGB", (RONG, CAO))
    rnd = np.random.default_rng(3); giot = [(rnd.uniform(0, RONG), rnd.uniform(0, CAO), rnd.uniform(0.6, 1.0)) for _ in range(160)]
    def dang_mua(tt, t_canh):
        on = False
        for t0, k in hu_sk:
            if t_canh <= t0 <= tt and k in ("mưa", "tắt mưa"): on = (k == "mưa")
        return on

    for f in range(so_khung):
        tt = f / FPS
        c = next((x for x in ds if x["t0"] <= tt < x["t1"]), ds[-1])
        W, bc, cao_nv = c["W"], c["bc"], c["cao_nv"]
        tc, dai_canh = tt - c["t0"], c["t1"] - c["t0"]
        loi = next((l for l in c["loi"] if l["t0"] <= tt < l["t1"] + NGHI), None)
        the_gioi = c["nen_img"].copy()
        vi_tri = {}; mat_shot = None
        for ten, n in c["nvs"].items():
            cf = lay_nv(ten)
            x, dang_di, huong = n["x"], None, None
            for (a, b, x0, x1) in n["di"]:
                if tt >= b: x = x1
                elif tt >= a:
                    p = (tt - a) / (b - a); x = x0 + (x1 - x0) * p; dang_di = tt - a
                    huong = "phải" if x1 > x0 else "trái"
            tu_the = [tt_ for (a, tt_) in n["tu_the"] if a <= tt][-1]
            co_tt = 1.0
            tte = tu_the_cua(cf, tu_the)
            if dang_di is None and isinstance(tte, dict):
                mat_shot = tte["mat"]; continue
            if dang_di is not None:
                f_ = cf["đi"][int(dang_di / NHIP_BUOC) % 2]; lat = huong != cf["huong_di"]; co_tt = 0.97
                nhun = -abs(math.sin(dang_di * math.pi / NHIP_BUOC)) * cao_nv * 0.012
            else:
                ngam, mo = tte[0], tte[1]; f_ = ngam; lat = False; nhun = 0
                if mo is None: mo = mo_cua(ngam)
                if len(tte) > 2: co_tt = tte[2]
                if loi and loi["ai"] == ten and tt < loi["t1"] and mo:
                    k = tt - loi["t0"]
                    if "mieng" in loi: m = loi["mieng"]; f_ = mo if m[min(int(k * FPS), len(m) - 1)] else ngam
                    elif not im_lang(loi["noi"]) and (k / GIAY_MOI_TIENG) % 1 < 0.55 and k < loi["t1"] - loi["t0"] - 0.3: f_ = mo
            cy_f, co = theo_vi_tri(bc["chan"], x); chan_y = cy_f * H; co = round(co * 50) / 50
            cnv = cao_nv * co; h = hinh_nv(f_, cnv * co_tt, bc["mau"], lat)
            cx = x * W
            for r in n["rung"]:
                if 0 <= tt - r < 1.4: cx += math.sin((tt - r) * 70) * cao_nv * 0.006
            tho = 0 if dang_di is not None else math.sin(tt * 2.2 + len(ten)) * cao_nv * 0.002
            s = bong(int(cnv * 0.34), int(cnv * 0.045))
            the_gioi.paste(s, (int(cx - s.width / 2), int(chan_y - s.height / 2)), s)
            the_gioi.paste(h, (int(cx - h.width / 2), int(chan_y - h.height + nhun + tho)), h)
            vi_tri[ten] = (cx, chan_y, cnv)
        if c["tien_canh"] is not None: the_gioi.paste(c["tien_canh"], (0, 0), c["tien_canh"])

        # máy quay
        can = None
        for (a, ai) in c["can"]:
            if a <= tt: can = ai
        if can in vi_tri:
            mx, cy0, cnv = vi_tri[can]; kh = cnv * 0.62; my = cy0 - cnv * 0.80
        else:
            kh = bc["khung"] * H * (1 - 0.05 * tc / dai_canh)
            trong = [v for v in vi_tri.values() if 0 <= v[0] <= W] or [(W / 2, bc["chan"] * H if not isinstance(bc["chan"], list) else H * 0.75, cao_nv)]
            mx = sum(v[0] for v in trong) / len(trong); my = sum(v[1] - v[2] * 0.5 for v in trong) / len(trong) + kh * 0.06
        if cam is None or canh_truoc is not c: cam = [mx, my, kh]
        else:
            k_ = 0.07; cam = [cam[0] + (mx - cam[0]) * k_, cam[1] + (my - cam[1]) * k_, cam[2] + (kh - cam[2]) * k_]
        canh_truoc = c
        ch_ = min(cam[2], H); cw_ = ch_ * RONG / CAO
        if cw_ > W: cw_ = W; ch_ = cw_ * CAO / RONG
        cx_ = min(max(cam[0], cw_ / 2), W - cw_ / 2); cy_ = min(max(cam[1], ch_ / 2), H - ch_ / 2)
        khung = the_gioi.crop((int(cx_ - cw_ / 2), int(cy_ - ch_ / 2), int(cx_ + cw_ / 2), int(cy_ + ch_ / 2))).resize((RONG, CAO), Image.BILINEAR)
        if mat_shot:   # cắt sang cận khuôn mặt
            khung = c["nen_mo"].copy(); fm = hinh_nv(mat_shot, CAO * 0.96, bc["mau"], False)
            khung.paste(fm, ((RONG - fm.width) // 2, CAO - fm.height), fm)

        for t0, k in hu_sk:
            if k == "rung" and 0 <= tt - t0 < 0.6:
                bien = int(14 * (1 - (tt - t0) / 0.6)); dx_, dy_ = rnd.integers(-bien, bien + 1, 2)
                khung = khung.transform(khung.size, Image.AFFINE, (1, 0, dx_, 0, 1, dy_), resample=Image.BILINEAR)
        if dang_mua(tt, c["t0"]):
            khung = Image.blend(khung, den, 0.12); dm = ImageDraw.Draw(khung, "RGBA")
            for (gx, gy, v) in giot:
                y_ = (gy + tt * 1400 * v) % CAO; x_ = (gx - tt * 200 * v) % RONG
                dm.line([(x_, y_), (x_ - 6 * v, y_ + 30 * v)], fill=(200, 210, 230, int(110 * v)), width=2)
        khung.paste(den, (0, 0), toi_vien)
        for t0, k in hu_sk:
            if k == "chớp" and 0 <= tt - t0 < 0.4: khung = Image.blend(khung, Image.new("RGB", khung.size, (255, 255, 255)), 0.85 * (1 - (tt - t0) / 0.4))
        if loi and not im_lang(loi["noi"]):
            d = ImageDraw.Draw(khung); dong, hang = [], ""
            for tu in chu_phu_de(loi["noi"]).split():
                thu = (hang + " " + tu).strip()
                if d.textlength(thu, font=font) > RONG * 0.86: dong.append(hang); hang = tu
                else: hang = thu
            dong.append(hang); y0 = CAO - 40 - len(dong) * 56
            for j, hh in enumerate(dong):
                d.text(((RONG - d.textlength(hh, font=font)) / 2, y0 + j * 56), hh, font=font, fill=(255, 225, 70), stroke_width=4, stroke_fill=(0, 0, 0))
        mo = min(1.0, tc / 0.35, (dai_canh - tc) / 0.35)
        if mo < 1: khung = Image.blend(Image.new("RGB", khung.size), khung, max(mo, 0))
        ff.stdin.write(khung.tobytes())
        if f % 250 == 0: print(f"   {f}/{so_khung}")
    ff.stdin.close(); ff.wait(); print(">> Xong:", ra); return ra

if __name__ == "__main__":
    lam_phim(sys.argv[1] if len(sys.argv) > 1 else os.path.join(THU_MUC, "kich_ban_tap1.txt"))

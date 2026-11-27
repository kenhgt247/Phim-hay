"""Sprite animation v2. Optional, validated packs; old images remain compatible."""
from pathlib import Path
from functools import lru_cache
import json, math, hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import uniform_filter1d

ROOT = Path(__file__).resolve().parents[1] / "kho" / "chuyen_dong"
MA = {"Hiền": "hien", "Kẻ lạ": "kela", "Hắc": "kela", "Lan": "lan", "Bố": "bo", "Mẹ": "me",
      "Tuấn": "danem", "Đàn em": "danem", "Tùng": "tung", "Hiền trẻ": "hientre", "Minh": "minh",
      "Thiếu tá Minh": "minh", "Tâm": "tam", "Anh Tâm": "tam", "Ngọc": "ngoc"}

def la_frame(f):
    return isinstance(f, str) and f.startswith("anim_") and Path(f).name == f and f.endswith(".png")

@lru_cache(maxsize=32)
def pack(ten):
    ma = MA.get(ten)
    if not ma: return {}
    try:
        data = json.loads((ROOT / (ma + ".json")).read_text(encoding="utf-8"))
        if data.get("version") != 1: return {}
        return data
    except (OSError, ValueError, AttributeError):
        return {}

@lru_cache(maxsize=64)
def frames(ten, kieu):
    p = pack(ten).get(kieu, {})
    if not isinstance(p, dict): return []
    fs = p.get("frames", [])
    if not isinstance(fs, list) or not fs or not all(la_frame(f) and (ROOT / f).is_file() for f in fs):
        return []
    return fs

def frame_di(ten, cu, huong_cu, huong, t, nhip):
    fs = frames(ten, "walk")
    if len(fs) == 8:
        i = int(max(0, t) / (2 * nhip) * len(fs)) % len(fs)
        return fs[i], huong != pack(ten)["walk"].get("direction", "phải")
    return cu[int(max(0, t) / nhip) % len(cu)], huong != huong_cu

def frame_dung(ten, pose, fallback, t, muc, noi):
    p = pack(ten).get("idle", {})
    fs = frames(ten, "idle")
    if len(fs) != 4 or p.get("pose") != pose: return fallback
    if noi and muc: return fs[min(3, 1 + muc)]
    phase = (t + int(hashlib.sha256(ten.encode()).hexdigest()[:4], 16) / 65535 * 3) % 4.3
    return fs[1] if 3.6 <= phase < 3.76 else fs[0]

def muc_mieng(rms):
    if len(rms) == 0: return np.zeros(1, dtype=np.uint8)
    env = uniform_filter1d(np.asarray(rms, dtype=float), size=3, mode="nearest")
    ref = max(float(np.percentile(env, 90)), 0.04)
    return np.where(env < max(.035, ref*.12), 0, np.where(env < ref*.60, 1, 2)).astype(np.uint8)

def tho(h, t, ten, noi=False):
    phase = (int(hashlib.sha256(ten.encode()).hexdigest()[:4], 16) % 100) / 100 * math.tau
    d = .004 * math.sin(t * 2.1 + phase)
    if noi: d += .0025 * math.sin(t * 5.2 + phase)
    ht = max(1, round(h.height * (1+d)))
    if ht == h.height: return h
    return h.resize((h.width, ht), Image.Resampling.BILINEAR)

# -*- coding: utf-8 -*-
"""Âm thanh tự tạo bằng code (không cần tải file): nhạc nền theo không khí, tiếng bước chân,
tiếng phố đêm, tiếng xe máy chạy qua, tiếng đồng hồ, tiếng mưa, tiếng điện thoại rung.
Nếu có file nhạc thật trong thư mục nhac/ (vd. nhac/cang_thang.mp3) thì dùng file đó thay cho nhạc tự tạo."""
import os, subprocess
import numpy as np

SR = 48000
GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rng = np.random.default_rng(7)

def _loc_thap(x, cat):           # lọc thông thấp đơn giản (cat: 0-1, nhỏ = trầm)
    y = np.empty_like(x); a = 0.0
    for i in range(0, len(x), 4096):
        seg = x[i:i + 4096]; out = np.empty_like(seg)
        for j, v in enumerate(seg):
            a += cat * (v - a); out[j] = a
        y[i:i + 4096] = out
    return y

def loc_thap(x, hz):             # bản nhanh dùng FFT
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (f / hz) ** 4); return np.fft.irfft(X, len(x)).astype(np.float32)

def loc_dai(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= ((f > lo) & (f < hi)).astype(np.float32); return np.fft.irfft(X, len(x)).astype(np.float32)

def vang(x, giay=2.2, tron=0.35):  # tiếng vang (reverb)
    n = int(giay * SR); ir = rng.standard_normal(n).astype(np.float32) * np.exp(-np.arange(n) / (SR * giay / 5))
    ir = loc_thap(ir, 5000); ir /= np.abs(ir).sum() ** 0.5 * 20
    L = len(x) + n; F = 1 << (L - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, F) * np.fft.rfft(ir, F), F)[:len(x)].astype(np.float32)
    y = y / (np.abs(y).max() + 1e-9) * (np.abs(x).max() + 1e-9)
    return (x * (1 - tron) + y * tron).astype(np.float32)

def hz(note):                     # tên nốt -> tần số, vd "A3"
    ten = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    n = ten.index(note[:-1]); o = int(note[-1]); return 440 * 2 ** ((n + 12 * (o + 1) - 69) / 12)

def nen_dem(f, dai, am=0.5):       # tiếng nền kiểu dây đàn (pad)
    t = np.arange(int(dai * SR)) / SR; y = np.zeros_like(t, dtype=np.float32)
    for de in (-0.15, 0, 0.17):
        ph = 2 * np.pi * f * (1 + de / 100) * t
        y += (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)).astype(np.float32)
    return y / 3 * am

def phim_dan(f, dai, am=0.4):      # tiếng gảy kiểu piano nhẹ
    t = np.arange(int(dai * SR)) / SR
    y = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.6 for k in (1, 2, 3, 4)) * np.exp(-t * 3.2)
    return (y * am * np.minimum(1, t / 0.005)).astype(np.float32)

def bao(dai, vao=2.0, ra=2.0):
    n = int(dai * SR); e = np.ones(n, np.float32); a, b = int(vao * SR), int(ra * SR)
    e[:a] = np.linspace(0, 1, a); e[-b:] = np.minimum(e[-b:], np.linspace(1, 0, b)); return e

def nhac(kieu, dai):
    """Nhạc nền tự tạo. kieu: căng thẳng / bí ẩn / ấm áp / buồn"""
    tep = os.path.join(GOC, "nhac", {"căng thẳng": "cang_thang", "bí ẩn": "bi_an", "ấm áp": "am_ap", "buồn": "buon"}.get(kieu, kieu) + ".mp3")
    if os.path.exists(tep):
        raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", tep, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
        y = np.frombuffer(raw, np.float32)
        if len(y) == 0: return np.zeros(int(dai * SR), np.float32)
        y = np.tile(y, int(dai * SR / len(y)) + 1)[:int(dai * SR)]
        return (y / (np.abs(y).max() + 1e-9) * bao(dai, 1, 2)).astype(np.float32)
    n = int(dai * SR); y = np.zeros(n, np.float32); t = np.arange(n) / SR
    if kieu == "căng thẳng":
        y += nen_dem(hz("D2"), dai, 0.55) + nen_dem(hz("A2"), dai, 0.30) + nen_dem(hz("D#3"), dai, 0.10 * (0.5 + 0.5 * np.sin(t * 0.7)))
        for k in np.arange(0.5, dai - 0.3, 1.25):          # nhịp tim trầm
            i = int(k * SR); m = min(int(0.35 * SR), n - i); tt = np.arange(m) / SR
            nhip = np.sin(2 * np.pi * 52 * tt) * np.exp(-tt * 14)
            y[i:i + m] += nhip * 0.9
            j = i + int(0.22 * SR); m2 = min(m, n - j)
            if m2 > 0: y[j:j + m2] += nhip[:m2] * 0.55
        y = loc_thap(y, 1200)
    elif kieu == "bí ẩn":
        y += nen_dem(hz("A2"), dai, 0.45) + nen_dem(hz("E3"), dai, 0.25) + nen_dem(hz("C4"), dai, 0.10)
        y = loc_thap(y, 1500)
        for k, nt in zip(np.arange(1.0, dai - 1, 1.6), ["E5", "C5", "A4", "B4", "E5", "G4", "A4", "C5"] * 20):
            i = int(k * SR); p = phim_dan(hz(nt), min(2.5, (n - i) / SR), 0.22); y[i:i + len(p)] += p
    elif kieu == "buồn":
        hop = [("A2", "C4", "E4"), ("F2", "A3", "C4"), ("C3", "E4", "G4"), ("G2", "B3", "D4")]
        for k, (a, b, c) in enumerate(hop * 20):
            s = k * 4.0
            if s >= dai: break
            i = int(s * SR); m = min(int(4.5 * SR), n - i); seg = (nen_dem(hz(a), m / SR, 0.4) + nen_dem(hz(b), m / SR, 0.2) + nen_dem(hz(c), m / SR, 0.15)) * bao(m / SR, 1.2, 1.2)
            y[i:i + m] += seg
        y = loc_thap(y, 1800)
    else:  # ấm áp
        hop = [("C3", "E4", "G4", "B4"), ("A2", "C4", "E4", "G4"), ("F2", "A3", "C4", "E4"), ("G2", "B3", "D4", "F4")]
        for k, nhom in enumerate(hop * 20):
            s = k * 3.2
            if s >= dai: break
            i = int(s * SR); m = min(int(3.6 * SR), n - i)
            y[i:i + m] += (nen_dem(hz(nhom[0]), m / SR, 0.35) + nen_dem(hz(nhom[1]), m / SR, 0.12)) * bao(m / SR, 0.8, 0.8)
            for q, nt in enumerate(nhom[1:] + nhom[1:2]):
                j = i + int(q * 0.8 * SR)
                if j < n: p = phim_dan(hz(nt), min(2.0, (n - j) / SR), 0.25); y[j:j + len(p)] += p
        y = loc_thap(y, 3000)
    y = vang(y, 2.5, 0.4)
    return (y / (np.abs(y).max() + 1e-9) * bao(dai, 1.5, 2.0)).astype(np.float32)

def buoc_chan(manh=1.0):
    m = int(0.09 * SR); t = np.arange(m) / SR
    y = loc_dai(rng.standard_normal(m).astype(np.float32), 80, 900) * np.exp(-t * 55)
    y += np.sin(2 * np.pi * 70 * t) * np.exp(-t * 40) * 0.6
    return (y / (np.abs(y).max() + 1e-9) * 0.5 * manh).astype(np.float32)

def xe_may(dai=3.0):
    n = int(dai * SR); t = np.arange(n) / SR; giua = dai / 2
    f = 85 * (1 + 0.06 * np.tanh((giua - t) * 2))          # hiệu ứng xe lại gần rồi đi xa
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = (np.sign(np.sin(ph)) * 0.5 + np.sin(2 * ph) * 0.3).astype(np.float32)
    y = loc_thap(y + rng.standard_normal(n).astype(np.float32) * 0.3, 900)
    env = np.exp(-((t - giua) / (dai / 5)) ** 2)
    return (y / (np.abs(y).max() + 1e-9) * env * 0.5).astype(np.float32)

def nen_moi_truong(kieu, dai):
    n = int(dai * SR); y = np.zeros(n, np.float32)
    if kieu == "pho_dem":
        y += loc_thap(rng.standard_normal(n).astype(np.float32), 400) * 0.6     # tiếng ồn phố xa
        for k in np.arange(2.5, dai - 3, 9.0):                                  # xe máy chạy qua
            i = int(k * SR); x = xe_may(3.0); y[i:i + len(x)] += x[:n - i] * 0.6
        for k in np.arange(0.3, dai, 0.55):                                      # tiếng côn trùng rất nhỏ
            i = int(k * SR); m = min(int(0.12 * SR), n - i); tt = np.arange(m) / SR
            y[i:i + m] += np.sin(2 * np.pi * 4200 * tt) * (np.sin(2 * np.pi * 30 * tt) > 0) * np.exp(-tt * 20) * 0.04
    elif kieu == "van_phong":
        y += loc_thap(rng.standard_normal(n).astype(np.float32), 250) * 0.25    # tiếng phòng
        for k in np.arange(0.5, dai, 1.0):                                       # đồng hồ tích tắc
            i = int(k * SR); m = min(int(0.03 * SR), n - i); tt = np.arange(m) / SR
            y[i:i + m] += loc_dai(rng.standard_normal(m).astype(np.float32), 2000, 6000) * np.exp(-tt * 300) * 0.35
    elif kieu == "mua":
        y += loc_dai(rng.standard_normal(n).astype(np.float32), 400, 8000) * 0.5
    return y

def rung_dien_thoai():
    y = np.zeros(int(1.5 * SR), np.float32)
    for k in range(3):
        tt = np.arange(int(0.32 * SR)) / SR
        r = np.sign(np.sin(2 * np.pi * 160 * tt)) * np.sin(np.pi * tt / 0.32) * 0.22
        i = int(k * 0.5 * SR); y[i:i + len(r)] += r
    return y

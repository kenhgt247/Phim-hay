# Vẽ thêm miệng mở lên ảnh nhân vật ngậm miệng (dùng khi ChatGPT chỉ vẽ bản ngậm)
from PIL import Image, ImageDraw
def ve(src, dst, L, R, T, kieu):
    im = Image.open(src).convert("RGB"); S = 8
    x0, y0, w, h = int(L) - 6, int(T) - 8, int(R - L) + 12, 26
    reg = im.crop((x0, y0, x0 + w, y0 + h)).resize((w * S, h * S), Image.LANCZOS); d = ImageDraw.Draw(reg)
    l, r, t = (L - x0) * S, (R - x0) * S, (T - y0) * S
    if kieu == "cuoi":
        b = t + 11.5 * S
        d.chord((l, t - (b - t), r, b), 0, 180, fill=(110, 45, 45), outline=(70, 35, 30), width=int(1.3 * S))
        d.chord((l + 3 * S, t - (b - t) + 2 * S, r - 3 * S, b - 1.5 * S), 20, 160, fill=(220, 110, 105))
        d.rectangle((l + 2 * S, t, r - 2 * S, t + 2.2 * S), fill=(250, 248, 245))
    else:  # lạnh: miệng hé hình bầu dục
        d.ellipse((l + 1 * S, t - 1.5 * S, r - 1 * S, t + 8 * S), fill=(105, 40, 40), outline=(60, 30, 28), width=int(1.2 * S))
        d.ellipse((l + 4 * S, t + 3 * S, r - 4 * S, t + 7.5 * S), fill=(215, 105, 100))
        d.chord((l + 2.5 * S, t - 1 * S, r - 2.5 * S, t + 3 * S), 180, 360, fill=(248, 246, 242))
    im.paste(reg.resize((w, h), Image.LANCZOS), (x0, y0)); im.save(dst)
if __name__ == "__main__":
    ve("../mau/hien_nghe_ngam.png", "../mau/hien_nghe_mo.png", 808, 836, 112, "cuoi")
    ve("../mau/hien_nghelanh_ngam.png", "../mau/hien_nghelanh_mo.png", 810.5, 832.5, 120, "lanh")

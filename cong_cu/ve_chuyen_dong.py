"""Generate two character sprite sheets using existing Gemini credentials, validate and align.
Only approved character IDs; source sheets retained for visual QA. No key in output.
"""
import argparse, io, json, os, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from ve_kho import goi_api, tim_mau, KHOA, GIU_MAT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "kho" / "chuyen_dong"
SAMPLES = {
    "hien": ("hien_di_a", "hien_hien_ngam", "hien_hien_ngam.png"),
    "kela": ("kela_di_a", "kela_ngam", "kela_ngam.png"),
    "lan": ("lan_bang_3", "lan_tao", "lan_tao.png"),
    "tung": ("tung_bang_3", "tung_tao", "tung_tao.png"),
}
WALK = """Vẽ sprite sheet CHÍNH XÁC 4 cột x 2 hàng, 8 ô bằng nhau, đọc trái sang phải rồi hàng dưới.
Cùng một nhân vật nhìn nghiêng hoàn toàn sang PHẢI ở mọi ô, cùng màu và vóc dáng, bước đi trên cùng đường chân.
Thứ tự: 1 chân trái trước chạm đất; 2 hạ trọng tâm; 3 chân phải lướt qua chân trái; 4 nâng trọng tâm;
5 chân phải trước chạm đất; 6 hạ trọng tâm; 7 chân trái lướt qua chân phải; 8 nâng trọng tâm.
Tay đánh đối nghịch chân. Chu kỳ lặp, không cầm vật. Mỗi ô chỉ một người toàn thân. Không vạch chia ô, không chữ,
không số, không bóng, nền trắng #FFFFFF, cách biên từng ô ít nhất 7%, nhân vật cao khoảng 82% ô.
Giữ đầu, thân, chiều cao, kích cỡ, hướng nhìn y hệt. Không nhân bản người ngoài 8 ô."""
IDLE = """Vẽ sprite sheet CHÍNH XÁC 2 cột x 2 hàng, 4 ô bằng nhau; mỗi ô đúng một nhân vật toàn thân giống hệt
ảnh mẫu, giữ nguyên góc nhìn, tóc, nét, quần áo, tư thế tay và chân, tỷ lệ, vị trí. CHỈ đổi mắt và miệng.
Ô trên trái: mắt mở miệng ngậm; trên phải: mắt khép tự nhiên miệng ngậm; dưới trái: mắt mở miệng hé;
dưới phải: mắt mở miệng mở lớn khi nói, không đổi biểu cảm. Nền trắng #FFFFFF, không chữ, số, bóng hay đường phân ô,
chừa ít nhất 7% biên từng ô, người cao khoảng 82% ô."""

def split_sheet(im, rows, cols):
    """Fail on clipped/empty cells and major size discrepancy; align feet on common canvas."""
    im = im.convert("RGB")
    w,h = im.size
    cells = []
    for r in range(rows):
        for c in range(cols):
            cell = im.crop((c*w//cols, r*h//rows, (c+1)*w//cols, (r+1)*h//rows))
            a = np.asarray(cell).astype(np.int16)
            white = (a.min(2) > 230) & (a.max(2)-a.min(2) < 22)
            labels,_ = ndimage.label(white)
            edge = np.unique(np.concatenate((labels[0],labels[-1],labels[:,0],labels[:,-1])))
            bg = np.isin(labels, edge[edge != 0])
            fg = ~bg
            # Remove tiny isolated specks, retain main silhouette.
            comp,n = ndimage.label(ndimage.binary_dilation(fg, iterations=2))
            areas = ndimage.sum(fg, comp, range(1,n+1))
            if n == 0 or max(areas) < .035 * fg.size: raise ValueError("Ô trống/nhân vật quá nhỏ")
            fg &= np.isin(comp, [i+1 for i,x in enumerate(areas) if x >= max(areas)*.07])
            ys,xs = np.where(fg)
            if xs.min()<3 or ys.min()<3 or xs.max()>=cell.width-3 or ys.max()>=cell.height-3:
                raise ValueError("Nhân vật chạm mép ô; cần vẽ lại")
            alpha = (ndimage.gaussian_filter(fg.astype(float),.5)*255).astype(np.uint8)
            rgba = Image.fromarray(np.dstack((a.astype(np.uint8),alpha)), "RGBA")
            cells.append(rgba.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1)))
    hs = [x.height for x in cells]
    if max(hs)/min(hs)>1.30: raise ValueError("Tỷ lệ chiều cao giữa các frame lệch quá lớn")
    scale = 480/max(hs)
    res = [x.resize((max(1,round(x.width*scale)),max(1,round(x.height*scale))),Image.Resampling.LANCZOS) for x in cells]
    width = max(x.width for x in res)+12
    out=[]
    for x in res:
        frame=Image.new("RGBA",(width,480),(0,0,0,0))
        frame.alpha_composite(x,((width-x.width)//2,480-x.height))
        out.append(frame)
    return out

def make(ma, force=False):
    OUT.mkdir(parents=True,exist_ok=True)
    mf=OUT/(ma+".json")
    if mf.exists() and not force:
        old=json.loads(mf.read_text(encoding="utf-8"))
        if all((OUT/f).is_file() for k in ("walk","idle") for f in old.get(k,{}).get("frames",[])) and all(old.get(k,{}).get("frames") for k in ("walk","idle")):
            print("Đã có pack, dùng lại"); return
    if not KHOA: raise RuntimeError("Thiếu GEMINI_API_KEY")
    walk,idle,pose=SAMPLES[ma]
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        manifest={"version":1,"review":"pending_visual_review"}
        for kind,ref,prompt,rows,cols,ratio in (
            ("walk",walk,WALK,2,4,"16:9"),("idle",idle,IDLE,2,2,"3:4")):
            sample=tim_mau(ref)
            if not sample: raise FileNotFoundError(ref)
            print("Vẽ sheet",ma,kind,flush=True)
            raw=goi_api(GIU_MAT+prompt,sample,ratio,"2K")
            sheet=Image.open(io.BytesIO(raw)).convert("RGB")
            sheet.save(tmp/f"{ma}_{kind}_sheet.jpg",quality=95)
            frames=split_sheet(sheet,rows,cols)
            names=[]
            for i,im in enumerate(frames):
                name=f"anim_{ma}_{kind}_{i:02d}.png"
                im.save(tmp/name)
                names.append(name)
            manifest[kind]={"frames":names,"direction":"phải"} if kind=="walk" else {"frames":names,"pose":pose}
        (tmp/mf.name).write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
        # Publish only a complete pack. Manifest last.
        for p in tmp.iterdir():
            if p.name!=mf.name: os.replace(p,OUT/p.name)
        os.replace(tmp/mf.name,mf)
    print("Đã tạo pack",ma,flush=True)

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--character",choices=SAMPLES,default="hien")
    cli.add_argument("--force",action="store_true")
    a=cli.parse_args()
    make(a.character,a.force)

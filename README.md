# Phim hoạt hình – Kho hình tự động

Kho này tự vẽ hình nhân vật và bối cảnh bằng Gemini API, tự tách bảng tư thế thành từng hình và xóa nền.

## Thư mục
- `danh_sach_hinh.txt` – danh sách hình cần vẽ (sửa ở đây để thêm hình mới)
- `mau/` – ảnh mẫu nhân vật đã có (gửi kèm để AI vẽ đúng mặt)
- `kho/goc/` – ảnh AI vẽ ra (nguyên bản)
- `kho/tach/` – từng tư thế đã tách, nền trong suốt (dùng để dựng phim)
- `kho/xem_truoc.png` – ảnh xem nhanh toàn bộ kho
- `phan_mem/` – phần mềm dựng phim

## Cài một lần
1. Vào https://aistudio.google.com → **Get API key** → **Create API key** → sao chép khóa.
2. Bật thanh toán cho khóa đó (Google AI Studio → Billing) – vẽ ảnh qua API không có gói miễn phí.
3. Vào kho này trên GitHub → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
   - Name: `GEMINI_API_KEY`
   - Secret: dán khóa vừa sao chép → **Add secret**

> Không dán khóa vào bất kỳ file nào hay gửi cho ai.

## Vẽ hình
1. Vào tab **Actions** → chọn **Vẽ kho hình** → **Run workflow**.
2. Lần đầu để "Vẽ tối đa" = `2` để thử. Ổn rồi thì để `30`.
3. Chờ chạy xong (dấu tích xanh), mở `kho/xem_truoc.png` để xem.

**Vẽ lại hình xấu:** Run workflow, gõ tên hình vào ô "Vẽ lại" (vd: `hien_bang_dung`).

# Xưởng Phim Hay – nhánh thử nghiệm 2.0 / render 1.2

## Đã cài đặt trong đợt 1
- CLI chọn 360p nhanh, 720p, 1080p; preview không TTS; kiểm tra trước khi dựng.
- Cache WAV theo nội dung, giọng và phiên bản gói VieNeu; ghi cache nguyên tử.
- Tệp tạm riêng từng công việc, lỗi TTS/FFmpeg không được báo thành công.
- Ducking nhạc dùng uniform_filter1d thay cho tích chập trực tiếp.
- Góc máy toàn, trung, cận, tiến, lùi, trái, phải và sắp nhân vật theo độ sâu chân.
- Phụ đề trắng, cỡ chữ theo độ phân giải. Workflow kiểm tra tên tệp, xuất artifact.
- Bộ kiểm thử và đoạn demo Hai Mặt độc lập; không thay nội dung tập gốc.

## Thử nghiệm
GitHub Actions → Dựng phim → Run workflow → chọn branch phim-hay-2.0.
Nhập demo_dien_anh.txt; chọn nhanh + preview để xem không có lời thoại.
Chọn 1080p và bỏ preview để xuất phim có giọng. Tệp nằm trong Artifacts/phim, không commit MP4 vào nhánh thử nghiệm.
Workflow Kiểm thử Xưởng Phim tự chạy khi thay đổi mã. Xem log và artifact demo-dien-anh.

## Chạy máy cá nhân
    pip install pillow numpy scipy requests vieneu
    python phan_mem/lam_phim.py phan_mem/demo_dien_anh.txt --check
    python phan_mem/lam_phim.py phan_mem/demo_dien_anh.txt --preview --quality nhanh
    python phan_mem/lam_phim.py phan_mem/demo_dien_anh.txt --quality 1080p

Cần FFmpeg/FFprobe, Python 3.11, font tiếng Việt. Đặt PHIM_CACHE_GIONG nếu muốn đổi nơi lưu cache. Đổi PHIM_TTS_PROFILE khi thay model/cấu hình ngoài phiên bản gói.

## Chưa làm
Rig xương, chu kỳ bước 6–8 hình, viseme tiếng Việt, parallax thật, timeline, cache phân cảnh, object storage, thay PAT localStorage và giao diện điều khiển theo job ID. Chỉ hợp nhất main sau khi xem phim mẫu và chạy kiểm thử thành công. Chưa có benchmark hiệu năng.

# Chuyển động 2.0 – đợt 2
- Engine đọc pack kho/chuyen_dong/<ma>.json. 8 frame đi, 4 frame đứng (mắt mở/khép, miệng hé/mở).
- Tự dùng ảnh cũ nếu chưa có pack hoặc tư thế không khớp. Thở nhẹ neo chân; miệng 3 mức RMS, chưa phải nhận dạng âm vị.
- API dùng GEMINI_API_KEY sẵn có, mỗi lần tạo tối đa hai sheet. Không gọi API trong vòng render.
- Sheet được kiểm tra ô trống, chạm mép, sai chiều cao; căn đáy và kích thước canvas đồng nhất. Kiểm tra thị giác vẫn bắt buộc.
- Workflow Vẽ bộ chuyển động AI chỉ chạy trên phim-hay-2.0; tự chạy khi cập nhật generator, hoặc Run workflow sau khi workflow có trên main. Artifact chứa demo và sheet/frame; pack được lưu trên nhánh thử nghiệm, không merge.
- Demo dùng Hiền, 720p không lời thoại, có nhạc. Chưa có rig xương, cử động tay độc lập, đi bộ foot-lock vật lý, viseme tiếng Việt. Các frame AI cần kiểm duyệt nhận dạng và dáng.

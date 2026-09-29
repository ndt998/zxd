# Morning Pyramid Workout — GitHub Pages

Trang web bài tập kim tự tháp buổi sáng (nguồn: Saitama Fitness – 30 Day Discipline Challenge).
Giao diện tiếng Việt • Giọng đọc audio: nữ, tiếng Anh, tràn đầy năng lượng + nhạc nền nhẹ tổng hợp.

## Cấu trúc (deploy nguyên thư mục này lên GitHub Pages)

```
index.html          # toàn bộ app (CSS + JS inline, không cần thư viện ngoài)
audio/              # 9 file mp3 (giọng nữ + nhạc nền + beep giữ nhịp)
images/             # 9 ảnh minh họa hoạt họa
build_audio.py      # (nguồn) script tổng hợp audio – không cần deploy
raw/                # (nguồn) voice thô – không cần deploy
manifest.json       # bảng thời lượng audio
```

## Deploy lên GitHub Pages (3 bước)

1. Tạo repo mới trên GitHub (vd: `pyramid-workout`).
2. Upload **toàn bộ nội dung** thư mục này (`index.html`, `audio/`, `images/`, …) vào nhánh `main`
   (kéo-thả trên web UI hoặc `git add . && git commit -m "init" && git push`).
   *Không cần đổi đường dẫn nào — mọi tài nguyên đều dùng đường dẫn tương đối.*
3. Vào **Settings → Pages → Build and deployment**: Source = *Deploy from a branch*,
   Branch = `main`, folder = `/ (root)` → Save. Đợi ~1 phút, mở link
   `https://<username>.github.io/<repo>/`.

> Mẹo: nếu muốn dùng nhánh `gh-pages` hoặc thư mục `/docs` cũng được — chỉ cần giữ
> `index.html` nằm cùng cấp với `audio/` và `images/`.

## Bảng audio

| File | Thời lượng | Nội dung |
|---|---|---|
| `01_intro.mp3` | 0:18 | Chào mừng + mẹo uống nước/thở sâu |
| `02_pushups.mp3` | 1:07 | 20 push ups — beep mỗi 2,5 s/rep, cue halfway/last-10, khen cuối bài |
| `03_squats.mp3` | 1:30 | 30 air squats — beep mỗi 2,5 s/rep |
| `04_mountain.mp3` | 1:56 | 40 mountain climbers — beep mỗi 2,5 s/rep |
| `05_jacks.mp3` | 2:17 | 50 jumping jacks — beep mỗi 2,5 s/rep |
| `06_highknees.mp3` | 2:43 | 60 high knees — beep mỗi 2,5 s/rep |
| `07_plank.mp3` | 2:24 | 2 phút plank — cổ vũ mỗi 30 s, đếm ngược 10→1, kết buổi |
| `rest_30s.mp3` | 0:32 | Nghỉ 30 s (dùng 5 lần): 15 s halfway, 25–30 s đếm ngược 5→0 |
| `full_workout.mp3` | 15:06 | Bản ghép toàn buổi (intro → 6 bài → 5 nghỉ → plank) để nghe offline |

Nhạc nền: 3 biến thể tổng hợp bằng numpy/ffmpeg (bright cho bài tập, calm cho intro/nghỉ,
steady cho plank), tự động hạ âm lượng (ducking) khi giọng đọc nói.

## Tính năng trang web

- Player toàn buổi: phát lần lượt intro → bài 1 → nghỉ → … → plank, tự chuyển bài,
  tô sáng card đang phát; tua/âm lượng; từng card có nút nghe riêng.
- Lịch tháng ở cuối trang: bấm vào ngày để ghi nhận **toàn phần (100%)** hoặc
  **một phần (% / số phút)**; thời điểm bấm tick được lưu kèm.
- Streak 🔥: chuỗi ngày liên tiếp có tick (tính theo ngày của thời điểm tick),
  streak dài nhất, tổng buổi, % tháng này; cảnh báo nếu hôm nay chưa tick.
- Dữ liệu lưu trong `localStorage` trình duyệt — dùng nút **Xuất/Nhập backup (JSON)**
  để giữ an toàn khi đổi máy / xóa dữ liệu duyệt web.

## Tái tạo audio (tuỳ chọn)

```bash
pip install numpy imageio-ffmpeg
# đặt lại voice thô vào raw/ (tạo bằng TTS giọng nữ, xem build_audio.py)
python3 build_audio.py
```

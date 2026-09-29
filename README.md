# Morning Pyramid Workout

Trang tĩnh dành cho GitHub Pages. Tổng thời lượng 10 phút 22 giây: mở đầu 12 giây, hít đất 55 giây, squat 75 giây, leo núi 70 giây, jumping jacks 70 giây, nâng cao đùi 70 giây, plank 120 giây và năm lần nghỉ 30 giây.

## Đăng lên GitHub Pages

1. Giải nén, đưa **toàn bộ nội dung thư mục `pyramid-workout`** lên nhánh chính của repository. `index.html`, `audio/` và `images/` cần cùng cấp như trong gói.
2. Mở **Settings → Pages → Build and deployment → Deploy from a branch**, chọn nhánh chính và thư mục `/ (root)`, rồi lưu.
3. Truy cập đường dẫn Pages được GitHub cung cấp. Nhấn **Bắt đầu tập** để trình duyệt cho phép phát âm thanh.

Bạn cũng có thể đặt nguyên thư mục `pyramid-workout` trong repository rồi chọn thư mục `/docs` bằng cách đổi tên nó thành `docs`.

## Nội dung

- `index.html`: giao diện, đồng hồ, điều khiển, nhắc tư thế, lịch tập và streak.
- `audio/*.mp3`: 8 tệp giọng đọc tiếng Anh (mở đầu, sáu bài, một mẫu nghỉ 30 giây dùng lại năm lần). Thời lượng được đặt theo đồng hồ của trang.
- `images/*.webp`: sáu tranh minh họa hoạt họa tương ứng.

Đếm theo từng lần đưa gối ở mountain climbers và high knees. Khi tạm dừng trang hoặc chuyển sang ứng dụng khác, đồng hồ dừng để bạn không bỏ lỡ bài. Nhịp đếm là gợi ý, ưu tiên tư thế đúng và điều chỉnh bài theo sức của mình.

## Lịch và ghi nhận

- Ở cuối trang, chọn **Toàn phần** hoặc **Một phần**. Với buổi tập một phần, nhập số phút đã tập; trang tính phần trăm trên tổng 10 phút 22 giây.
- Bấm **Ghi nhận lúc này** để lưu đúng ngày và giờ hiện tại trên thiết bị. Trang không tự ghi nhận khi đồng hồ chạy hết và không cho ghi nhận lùi ngày.
- Nếu ghi nhận nhiều lần trong ngày, thời lượng được cộng lại và giới hạn mức hoàn thành trong ngày ở 100%. Ngày có ít nhất một lần tập lớn hơn 0 được tính vào streak; ngày hôm nay chưa tập thì streak của ngày hôm qua vẫn hiển thị cho đến hết ngày hôm nay.
- Dữ liệu nằm trong `localStorage` của đúng trình duyệt và địa chỉ trang này. Đổi thiết bị, xóa dữ liệu trình duyệt, dùng chế độ riêng tư hoặc chuyển sang domain khác sẽ không tự đồng bộ lịch tập.

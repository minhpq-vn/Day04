# sentiment_analyzer tool

Phân tích cảm xúc, mức độ rủi ro truyền thông và thống kê chủ đề nổi bật từ danh sách các bài đăng mạng xã hội hoặc văn bản thảo luận.

## When to use
Sử dụng khi người dùng yêu cầu:
- Phân tích sentiment (tích cực / tiêu cực / trung lập) của các thảo luận.
- Đánh giá chỉ số rủi ro khủng hoảng truyền thông.
- Trích xuất từ khóa / chủ đề lặp lại nhiều và đề xuất hành động tiếp theo cho team PR / Marketing.

## Input Arguments
- `items` (list[dict]): Danh sách bài đăng thu thập được từ `social_search` hoặc `timeline` (mỗi item có `title`, `summary`, `url`, `source`, `metrics`).
- `query` (str): Từ khóa / Thương hiệu đang được theo dõi.

## Output
Trả về dictionary gồm:
- `total_posts`: Tổng số bài đăng được phân tích.
- `sentiment_breakdown`: Tỷ lệ/Số lượng bài Tích cực (Positive), Tiêu cực (Negative), Trung lập (Neutral).
- `overall_sentiment`: Cảm xúc chủ đạo (Positive, Negative, Mixed, Neutral).
- `risk_score`: Thang điểm rủi ro truyền thông (0 - 100%).
- `key_issues`: Các chủ đề / vấn đề nổi bật.
- `recommended_actions`: Đề xuất hành động ứng phó cho brand/team.

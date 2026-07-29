# Day 04 Lab v2 — Research Agent Tool Eval

## 👥 BẢNG PHÂN VAI & FILE ĐẢM NHẬN

**Chủ đề:** Social Listening Monitor — research/monitoring agent theo dõi tài khoản và các chủ đề được bàn luận trên X/Twitter. Agent chỉ kết luận từ dữ liệu tool trả về, không tự khẳng định tín hiệu không có bằng chứng.

| Vai trò | File đảm nhận | Nhiệm vụ chính | Người đảm nhận | Mã sinh viên |
|---|---|---|---|---|
| **Role 1: Product Architect** | `data/eval_group.json` | Xác định MVP, viết đúng 10 team eval (5 single-turn, 5 multi-turn), bảo vệ fixed base eval. | Đặng Minh Quang | 2A202601108 |
| **Role 2: Tool Engineer** | `tools/social_search/tool.py` và tool mới | Kiểm tra RapidAPI Twitter API45, bổ sung tool/`TOOL.md`, bảo đảm tool trả lỗi thay vì crash. | Nhữ Văn Hùng | 2A202601372 |
| **Role 3: Prompt Engineer** | `artifacts/system_prompt.md` | Viết guardrails, routing và quy tắc tổng hợp; chỉ đổi prompt theo hypothesis đã ghi. | Phạm Quốc Minh | 2A202601494 |
| **Role 4: Core Developer / Integrator** | UI, `chat.py`, `tools/__init__.py`, `artifacts/tools.yaml` | Tích hợp tool, dựng UI/trace, đồng bộ declaration và chạy eval. | Nguyễn Văn Hưng | 2A202601284 |
| **Role 5A: Trace Analyst** | `analysis/base_runs.csv`, `artifacts/version_log.csv` | Phân tích run JSON, failure, metric/hash và ghi evidence v0–v3. | Đỗ Việt Tùng | 2A202601876 |
| **Role 5B: Flowchart & Report Architect** | `artifacts/REPORT.md` | Vẽ luồng monitoring, chuẩn bị report/demo có dẫn chứng run thật. | Bùi Thu Trang | 2A202601758 |

Mỗi người ưu tiên file mình phụ trách. Nếu rename tool, chỉ đồng bộ field tên tool trong fixed eval; không sửa query, expected arguments hoặc expected behavior của `data/eval_base.json`.

## Brief

Trong lab này, nhóm build **Social Listening Monitor**: research/monitoring agent tìm bài X/Twitter theo keyword, thương hiệu, sản phẩm, hashtag, sự kiện hoặc đối thủ, rồi tổng hợp tín hiệu thành brief cho Marketing, PR, Product hoặc Customer Support.

MVP: search bài theo keyword, chọn `Latest`/`Top`, tóm tắt sentiment và chủ đề chính, xuất brief có link nguồn. `social_search` dùng RapidAPI Twitter API45; chỉ gọi `timeline`, `lookup`, `fetch`, `format`, `clarify`, `policy` hoặc `send` khi thật sự phù hợp.

Điều cần học không phải là "chatbot trả lời hay". Điều cần học là vòng lặp evidence-driven:

1. Chạy baseline bằng API thật.
2. Đọc run JSON để biết sai tool, sai args, thiếu hỏi lại, hoặc gọi tool thừa.
3. Sửa `artifacts/system_prompt.md` hoặc `artifacts/tools.yaml`.
4. Chạy lại và ghi versioning.
5. Tự viết thêm eval case để đo những lỗi nhóm quan tâm.
6. Viết report dựa trên log thật, không dựa vào cảm giác.

## Scope

Nhiệm vụ bắt buộc:

- Setup chạy được bằng provider thật.
- Agent có ít nhất 5 tool trong `artifacts/tools.yaml`.
- Chạy base eval.
- Tối ưu ít nhất 3 vòng sau baseline: `v1`, `v2`, `v3`.
- Ghi `artifacts/version_log.csv`.
- Viết thêm ít nhất 1 tool mới (kèm `TOOL.md`, đăng ký trong `tools/__init__.py` và `tools.yaml`).
- Tự viết đúng 10 eval case vào `data/eval_group.json`: 5 single-turn + 5 multi-turn.
- Nộp run JSON, transcript JSON, report.
- Có UI chạy được. Khuyến nghị Streamlit để làm nhanh, nhưng nhóm có thể dùng bất kỳ framework nào và tự chọn nền tảng deploy phù hợp.
- Hoàn thành `artifacts/REPORT.md`: Phần A xong trước 16:30 để làm tài liệu phụ trợ khi demo; Phần B hoàn thiện sau để nộp bài.

UI là deliverable core, không phải bonus. Starter không cung cấp `app.py`; nhóm tự tạo UI bằng framework đã chọn.

Optional/advanced tools có sẵn (không tính là tool mới của team; giữ declaration vẫn có thể đổi routing):

- `send`: gửi text lên Telegram; live-send là optional.
- `policy`, `papers`, `paper_text`: tải/trích PDF; đều optional.

Điểm bonus dành cho team hoàn thành UI bắt buộc **và** tự viết thêm hơn 3 tool mới. UI riêng lẻ hoặc các optional tool có sẵn không được tính là bonus.

## Bằng chứng tối thiểu trên UI

UI tốt không chỉ cần "có chat". Mỗi demo nên nhìn được:

- request và response cuối cùng;
- trace của từng tool: tên tool, args, round/status, result/error;
- transcript/run/artifact_version để biết đang xem version nào;
- cùng một scenario demo được chạy qua nhiều prompt/tool version để thấy cải thiện rõ ràng.

Nếu chọn Streamlit, cài và ghi `streamlit>=1.30.0` vào `requirements.txt`. Tạo `app.py` tái sử dụng `run_model_tool_loop` trong `chat.py`, hiển thị `rounds/tool_events`, và lưu transcript thay vì viết một agent loop khác. Chạy `streamlit run app.py`; PASS khi mở được `http://localhost:8501`. Framework khác dùng contract tương đương và entrypoint của nhóm.

## Deploy để team khác test

UI chạy local chỉ đủ cho máy của team build; nếu team khác test từ máy khác thì phải có URL truy cập được. Framework hay nền tảng deploy nào cũng được, miễn là người ngoài máy trình chiếu mở được.

Cách nhanh nhất cho link tạm là Cloudflare Tunnel:

```bash
cloudflared tunnel --url http://localhost:8501
```

Lấy URL `trycloudflare.com` được sinh ra, paste vào `REPORT.md` phần A, rồi test lại bằng browser hoặc device khác trước showdown. Tunnel chỉ là giải pháp tạm thời; đừng để lộ secrets hoặc dữ liệu nhạy cảm trong UI public. Chi tiết cài đặt và lưu ý bảo mật nằm ở `TOOL-SETUP.md`.

## Thiết kế tool cũng là một phần của prompt engineering

Không chỉ prompt quyết định kết quả. Tên tool và mô tả tool cũng là một phần của interface với model.

Ưu tiên:

- tên tool phản ánh đúng intent;
- mô tả nói rõ khi nào dùng / khi nào không dùng;
- mô tả nêu convention cho arguments và default quan trọng;
- action tool phải nêu rõ confirmation boundary.

Nếu đổi tên tool, phải sync đồng bộ các file sau:

1. `artifacts/system_prompt.md`
2. `artifacts/tools.yaml`
3. `tools/<tool_name>/TOOL.md`
4. `tools/__init__.py`
5. `data/eval_base.json`
6. `data/eval_research_extension.json`
7. `data/eval_group.json` nếu case nhóm có nhắc đến tool đó
8. `artifacts/REPORT.md` và demo/poster text

Trong fixed eval, chỉ đổi field tên tool để đồng bộ rename; không sửa query, expected args hoặc expected behavior. Không sync đủ thì eval dễ báo `not declared in tools.yaml`, hoặc model và grader sẽ nói hai thứ khác nhau.

## Các file quan trọng

| Path | Mục đích |
|---|---|
| `artifacts/system_prompt.md` | instruction cho agent |
| `artifacts/tools.yaml` | tên, mô tả và schema của tool |
| `artifacts/version_log.csv` | giả thuyết và metric theo version |
| `artifacts/REPORT.md` | tài liệu demo và bằng chứng nộp bài |
| `data/eval_base.json` | base eval cố định |
| `data/eval_group.json` | 10 case do nhóm tự viết |
| `tools/<tool_name>/` | `TOOL.md` + implementation |
| `scripts/preflight_provider.py` | kiểm tra provider |

## Tool tracks

Contract tool cho Social Listening Monitor phải nêu cả lúc dùng và không dùng tool.

Core tools:

- `social_search`: tìm bài theo keyword/brand/hashtag; `Latest` cho monitoring mới nhất, `Top` cho bài nổi bật/tương tác cao.
- `timeline`: lấy bài gần đây của **một tài khoản cụ thể**, không thay thế search chủ đề.
- `clarify`: hỏi lại khi thiếu brand/keyword, account, timeframe, nền tảng hoặc xác nhận yes/no.
- `lookup`: chỉ tìm web/news khi cần ngữ cảnh ngoài social posts.
- `fetch`: đọc URL cụ thể đã được nêu hoặc cần kiểm chứng.
- `format`: định dạng dữ liệu đã có thành digest, không bịa bài đăng hay metrics.

Optional/advanced tools có sẵn:

- `send`: gửi text lên Telegram channel.
- `policy`: tìm trong company policy markdown nội bộ.
- `papers`: tìm paper trên arXiv.
- `paper_text`: tải PDF arXiv và trích text cục bộ.

## Setup

Xem chi tiết key, smoke test, và lưu ý Windows trong [TOOL-SETUP.md](TOOL-SETUP.md).

Tóm tắt nhanh:

```bash
cd starter_v0
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
test -f .env || cp .env.example .env
```

Mở `.env`, điền ít nhất key của model provider rồi lưu file. Sau đó mới chạy:

```bash
python scripts/preflight_provider.py --provider openrouter
```

Không ghi đè `.env` đã có. Nếu dùng provider khác, thay `openrouter` trong mọi command; xem lệnh Windows và quicktest chi tiết trong [TOOL-SETUP.md](TOOL-SETUP.md).

## Step 1 — Run baseline

Run the fixed base eval as `v0`:

Lưu ý: eval thực thi tool thật. Case Telegram trong base chỉ chấm `clarify(response_type="yes_no")`; để Telegram credentials unset trong mọi `run_eval`.

```bash
python run_eval.py --provider openrouter --version v0 --suite base --eval-cases data/eval_base.json
```

Đọc các trường chính trong run JSON:

- `summary.case_accuracy`
- `summary.tool_routing_accuracy`
- `summary.argument_accuracy`
- `summary.multiturn_accuracy`
- `summary.provider_error_cases`
- `summary.measured_cases`
- `results[*].result.failures`
- `results[*].result.observed_mismatch`

Điều kiện để metric có giá trị trong suite đang report:

- `provider_error_cases` phải bằng `0`.
- `measured_cases` phải bằng `total_cases`.
- `tool_results` có error phải được review thủ công; PASS ở routing không có nghĩa là tool chạy đúng.

Run JSON cũng lưu `artifact_version`, `prompt_hash`, `tools_hash`, actual tool calls, và actual tool results. Đó là evidence chính cho report.

**Phân vai v0:** Role 4 chạy và lưu run; Role 5A đọc failure/mismatch/tool call, Role 1 xác nhận base eval không bị sửa, Role 2 kiểm tra lỗi tool. Role 3 và 5B chỉ ghi evidence/candidate hypothesis, chưa tối ưu artifact.

Optional: parse run JSON into a flat CSV table for analysis:

```bash
python scripts/parse_runs.py runs/ --output analysis/base_runs.csv
```

## Step 2 — Fix one thing

Trong từng vòng tối ưu routing, chỉ sửa:

- `artifacts/system_prompt.md`
- `artifacts/tools.yaml`

Không sửa cases trong `data/eval_base.json`, ngoại trừ field tên tool khi rename theo checklist đồng bộ ở trên.

Đây là giới hạn cho mỗi thí nghiệm prompt/tool declaration, không cấm nhóm viết tool mới. Với tool mới, phải có `TOOL.md`, `tool.py`, đăng ký trong `tools/__init__.py`, thêm declaration vào `tools.yaml`, rồi smoke-test trực tiếp.

Method, not memorized answers:

1. Mở run JSON. Với mỗi case fail, đọc `observed_mismatch`, `failures`, `actual_tool_calls`, `tool_results`.
2. Phân loại failure: sai tool, sai argument, thiếu hỏi lại, sai confirmation boundary hoặc gọi tool thừa.
3. Đặt một hypothesis có thể kiểm chứng, truy được tới case ID/evidence của run trước.
4. Chỉ sửa `artifacts/system_prompt.md` **hoặc** `artifacts/tools.yaml` theo hypothesis đó.
5. Chạy một version, so metric trước/sau, rồi ghi version log.

## Step 3 — Run 3 optimization versions

Không chạy cả ba lệnh liên tiếp. Các hypothesis sau chỉ là candidate; chỉ áp dụng khi failure của version ngay trước đó xác nhận. Nếu không khớp, ghi hypothesis thực tế vào `version_log.csv`.

| Version | Hypothesis cần kiểm chứng | Một thay đổi trước run | Evidence cần so | Chủ trách nhiệm |
|---|---|---|---|---|
| **v0** | Baseline chưa có kết luận, cần đo routing/arguments thực tế. | Không tối ưu trước run. | 4 metric, `provider_error_cases=0`, `measured_cases=total_cases`, hashes và từng failure. | Role 4, 5A |
| **v1** | Nếu nhầm `timeline`/`lookup` với `social_search` hoặc nhầm `Latest`/`Top`, routing rule/convention `search_type` chưa rõ. | Sửa prompt **hoặc** declaration để phân biệt search chủ đề, account, Latest và Top. | `tool_routing_accuracy`, `argument_accuracy`, actual calls. | Role 3/4, 5A |
| **v2** | Nếu agent tự đoán brand/keyword/account/timeframe còn thiếu, điều kiện `clarify` chưa rõ. | Sửa prompt **hoặc** declaration, buộc hỏi thông tin thiếu. | `multiturn_accuracy`, `missing_info`, tool thừa. | Role 3, 1, 5A |
| **v3** | Nếu agent gọi `lookup`/`fetch` thừa, trộn suy luận với dữ liệu, hoặc tự `send`, boundary/priority tool chưa rõ. | Sửa prompt **hoặc** declaration, ưu tiên social data và confirm trước `send`. | `case_accuracy`, `wrong_boundary`, `unnecessary_tool`, trace. | Role 3/4, 5B |

v1–v3 phải là thí nghiệm thật: có failure nguồn, hypothesis, artifact/hash và metric trước–sau. Artifact không đổi không được tính là một vòng tối ưu.

Sau khi đã sửa đúng một hypothesis, mới chạy lệnh của version tương ứng:

```bash
python run_eval.py --provider openrouter --version v1 --suite base --eval-cases data/eval_base.json
python run_eval.py --provider openrouter --version v2 --suite base --eval-cases data/eval_base.json
python run_eval.py --provider openrouter --version v3 --suite base --eval-cases data/eval_base.json
```

Sau mỗi run, fill `artifacts/version_log.csv`:

```text
version,author,changed_artifact,artifact_version,prompt_hash,tools_hash,reason,hypothesis,metric_name,metric_before,metric_after,run_file
```

Quan trọng: v1/v2/v3 phải là 3 vòng cải tiến thật, không phải 3 run copy-paste giống hệt nhau.

## Step 4 — Add team eval

`data/eval_group.json` phải có đúng 10 case:

- 5 single-turn dùng `query`
- 5 multi-turn dùng `turns`

Mỗi case cần:

- `id`
- `phase`: luôn `"B"`
- `failure_type`: một trong `wrong_tool`, `wrong_arg_value`, `wrong_boundary`, `unnecessary_tool`, `out_of_scope`, `missing_info`
- `expect`: `tool_calls` hoặc `no_tool`
- `metadata.what_it_tests`

File `data/eval_group.json` để trống có chủ đích vì phần team eval phải do chính nhóm tự thiết kế.
Cả template trong `starter_v0/` và `solution/` đều trống; điều đó không thay đổi yêu cầu đúng 10 case. Xem [2 case mẫu về schema](starter_v0/samples/eval_group.schema.example.json) (không tính vào 10 case và không nộp thay case của team). Với multi-turn, phần tử cuối của `turns` phải là user turn đang được chấm.

Role 1 viết và Role 5A review 10 case để bao phủ: keyword/hashtag search; `Latest` vs `Top`; timeline theo handle; brief có nguồn; thiếu keyword cần `clarify`; phân biệt brand/account; cần thêm web context; URL cần `fetch`; từ chối `send`; và xác nhận `send`. Không đưa API result giả vào expected behavior.

Run:

```bash
python run_eval.py --provider openrouter --version v3 --suite group --eval-cases data/eval_group.json
```

Optional extension eval — không phải điều kiện hoàn thành core; chỉ chạy khi team chọn dùng các capability built-in này:

```bash
python run_eval.py --provider openrouter --version v3 --suite extension --eval-cases data/eval_research_extension.json
```

Nếu đã bỏ optional declarations để isolate core, bật lại chúng trước khi chạy extension.

## Step 5 — Chat live

`chat.py` là cho tương tác multi-round thật. Nó log mỗi turn vào `transcripts/*.transcript.json`.

```bash
python chat.py --provider openrouter --version v3
```

Thử ít nhất 3 live turn: “Theo dõi thảo luận mới nhất về VinFast trên X”; một request thiếu keyword/timeframe rồi bổ sung ở lượt sau; và yêu cầu gửi brief để kiểm tra boundary hỏi lại/xác nhận. Brief phải nêu link nguồn có từ tool result và tách rõ dữ liệu quan sát với phân tích/suy luận.

## Chuẩn bị demo

Trước demo, team nên rehearse 3–5 scenario cụ thể để showcase được tool đã làm gì và version nào cải thiện gì.

Checklist tối thiểu:

- khóa artifact trước buổi demo;
- kiểm tra API key, quota, và link demo còn sống;
- mở sẵn logs/run JSON/transcript cần chiếu;
- chuẩn bị fallback run hoặc fallback transcript nếu mạng chập chờn;
- không để lộ secrets trong screenshot, log, hoặc poster;
- cùng một scenario nên được so sánh xuyên suốt v0 → later versions để thấy cải thiện rõ.

Vòng lặp làm việc nên là:

1. đổi một hypothesis;
2. chạy một version;
3. inspect evidence + hash;
4. ghi lại;
5. rồi mới đi tiếp.

Không nên chạy ba bản sao giống hệt nhau chỉ để có tên v1/v2/v3.

## Hoàn thiện report

Hoàn thành `artifacts/REPORT.md`. File này có 2 phần với deadline khác nhau:

- **Phần A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Xong trước 16:30 để làm tài liệu phụ trợ khi demo.
- **Phần B — Chi tiết / Bằng chứng**: bảng đầy đủ v0–v3, failure analysis, eval cases, live chat, reflection — dựa trên log thật. Có thể hoàn thiện sau buổi debate để nộp bài.

Khuyến nghị tối thiểu cho Phần A là markdown trong `REPORT.md`. Nếu muốn show mượt hơn, có thể làm thêm poster HTML/SVG 1 trang để trình bày cùng nội dung.

## Submit

Submit `starter_v0/` with:

- `artifacts/system_prompt.md`
- `artifacts/tools.yaml`
- `artifacts/version_log.csv` với ít nhất `v0`, `v1`, `v2`, `v3`
- `artifacts/REPORT.md`
- `data/eval_group.json` với đúng 10 team cases
- `runs/*.json`
- `analysis/*.csv` nếu có parse run logs
- `transcripts/*.transcript.json`
- implementation của tool mới, code UI, và dependency tương ứng

Do not submit `.env`, API keys, `.venv/`, hoặc cache/build output.
Kênh nộp, quy tắc đặt tên và deadline cuối theo thông báo của giảng viên; team cần xác nhận các thông tin này trước khi zip hoặc gửi repo link.

## Checkpoints — K4 buổi chiều (14:00–18:00)

0. **Kickoff — 14:00–14:15:** chia nhóm, phân vai và mở `starter_v0/`.
1. **Setup — 14:15–14:40:** chuẩn bị môi trường, API keys và chạy provider preflight.
2. **Baseline v0 — 14:40–15:15:** chạy base eval, đọc một failed trace, dựng UI local và ghi bốn metric.
3. **v1 + Tool — 15:15–15:50:** sửa một giả thuyết, hoàn thiện một tool mới, chạy v1 và cập nhật version log.
4. **Nghỉ — 15:50–16:05.**
5. **Eval + v2 — 16:05–16:30:** hoàn thành 10 team eval cases, evidence v2, ba kịch bản demo, Report A và rehearsal.
6. **Demo → Ship — 16:30–17:40:**
   - **Showdown — 16:30–17:15:** giới thiệu, live test và challenge.
   - **v3 + Report B — 17:15–17:35:** áp dụng feedback, chạy v3 và hoàn thiện report bằng evidence.
   - **Final gate — 17:35–17:40:** kiểm tra và chuẩn bị nộp `starter_v0/`.
7. **Kahoot Recap — 17:40–18:00.**

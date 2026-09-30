# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`, SLO `fast_successful_requests` (`config/slo.yaml`)
- Điều kiện và thời gian duy trì: `percentile(latency_ms, 95) > 3000ms` duy trì liên tục trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn ngưỡng SLO trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Latency trên dashboard, xác nhận P95/P99 và khoảng thời gian bắt đầu tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy `correlation_id` của request có `latency_ms` cao nhất.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh thời gian span `retrieval` và `generation` để xác định bước chậm.
- Mitigation tạm thời: nếu span `retrieval` chậm bất thường (nghi ngờ `rag_slow`), tắt incident/practice scenario liên quan bằng `python scripts/inject_incident.py --disable` hoặc `POST /incidents/rag_slow/disable`; nếu do prompt mới, rollback label `production` về version trước.
- Owner: `student-2A202602468`

## Alert 2

- Tên: `LowRetrievalSuccessRate`
- Severity: `critical`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: `tool_success_rate_pct` trong panel Errors, guardrail `retrieval_success_rate_pct_min: 90` (`config/slo.yaml`)
- Điều kiện và thời gian duy trì: tỉ lệ `tool_success == true` trên các request có `tool_name == "retrieval"` giảm dưới 90% trong 5 phút
- Ảnh hưởng tới người dùng: request trả lỗi 500 hoặc câu trả lời thiếu context vì bước retrieval thất bại
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Errors, xác nhận `tool_success_rate_pct` giảm và error rate tăng cùng khoảng thời gian.
  2. Lọc `data/logs.jsonl` với `event == "request_failed"` hoặc `tool_success == false`, lấy một `correlation_id`.
  3. Mở trace cùng `correlation_id`, kiểm tra span `retrieval` có bị lỗi hoặc raise exception không.
- Mitigation tạm thời: nếu nghi ngờ incident `tool_fail`, tắt bằng `POST /incidents/tool_fail/disable`; kiểm tra vector store/dependency retrieval trước khi mở lại traffic.
- Owner: `student-2A202602468`

## Alert 3

- Tên: `DailyCostBudgetExceeded`
- Severity: `warning`
- Duration: `10m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: tổng `response_sent.cost_usd` trong panel Cost, guardrail `daily_cost_usd_max: 2.5` (`config/slo.yaml`)
- Điều kiện và thời gian duy trì: `sum(cost_usd)` trong cửa sổ 60 phút vượt `2.5 USD`, xác nhận lại sau 10 phút để tránh cảnh báo giả do traffic tăng đột biến bình thường
- Ảnh hưởng tới người dùng: không ảnh hưởng trực tiếp latency, nhưng chi phí vận hành tăng bất thường, có thể do token output tăng đột biến trên mỗi request
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Cost và Tokens, xác nhận `cost_usd`/`tokens_out` tăng bất thường trong cùng khoảng thời gian.
  2. Lọc `data/logs.jsonl` theo `event == "response_sent"`, sắp xếp theo `tokens_out` hoặc `cost_usd` giảm dần, lấy `correlation_id` cao nhất.
  3. Mở trace cùng `correlation_id`, kiểm tra span `generation` có `usage_details.output` tăng bất thường so với các request khác không.
- Mitigation tạm thời: nếu nghi ngờ incident `cost_spike`, tắt bằng `POST /incidents/cost_spike/disable`; xem lại prompt version đang dùng nếu output dài bất thường sau khi promote label mới.
- Owner: `student-2A202602468`

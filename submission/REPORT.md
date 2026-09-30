# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên: Nguyễn Đức Thịnh**
- **MSSV: 2A202602468**
- **Lớp:** K4-L3B
- **Repository URL: https://github.com/thihngD/K4-L3-DAY13-NguyenDucThinh-2A202602468-Monitoring-LLMOps**
- **Commit SHA cuối:** `97aa02832a0251f7c79825fcca6a2098fd108348`
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602468`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` (`correlation_id=req-1a2b3c4d`) |
| PII redaction | `evidence/05-pii-redaction.png` (`correlation_id=req-5e5e5e5e`, 1 message chứa cả 4 loại PII) |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata (root) | `evidence/08a-trace-metadata-root.png` |
| Trace metadata (generation) | `evidence/08b-trace-metadata-generation.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt promote (production→v2) | `evidence/10a-prompt-production-v2.png` |
| Prompt rollback (production→v1) | `evidence/10b-prompt-production-v1.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 (FAILED: missing fields, correlation ID, enrichment; PASSED: PII scrubbing) | 100/100 (PASSED cả 4 mục) — `evidence/02-log-validator.png` | CP1 xong: correlation ID, enrichment, PII scrubbing |
| `validate_dashboard.py` | 6/6 panel hợp lệ | 6/6 panel hợp lệ — `evidence/03-dashboard-validator.png` | Dashboard contract đã đủ 6 panel từ đầu |
| `pytest` | 22 passed | 24 passed — `evidence/01-pytest.png` (commit `97aa028`) | Thêm 2 test CCCD/thẻ thanh toán cho `app/pii.py` |
| Số traces hợp lệ | | 51 root trace (`isRootObservation=true`) — `evidence/06-trace-list.png` | Vượt tối thiểu 10 traces yêu cầu |
| Số PII leak | 0 (validator báo 0, nhưng do thiếu field chứ chưa xác nhận scrub thật) | 0 — xác nhận cả 4 loại (email/điện thoại/CCCD/thẻ) trong cùng 1 message qua `evidence/05-pii-redaction.png` | |
| Latency P95 / TTFT P95 | Chưa đo (dashboard chưa parse do log thiếu field) | P95 ≈ 266ms / TTFT P95 ≈ 54ms — `evidence/11-dashboard-overview.png` | Đo bằng `scripts/render_dashboard.py` trên mẫu 20 request |
| Retrieval success rate | Chưa đo | 100% (`tool_success=true` trên toàn bộ request có retrieval) | `evidence/11-dashboard-overview.png` |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** `CorrelationIdMiddleware` (`app/middleware.py`) xóa contextvars cũ (`clear_contextvars`) đầu mỗi request, đọc header `x-request-id` nếu client gửi, ngược lại sinh `req-<8-hex>` bằng `uuid.uuid4().hex[:8]`; bind vào `structlog.contextvars` và lưu vào `request.state.correlation_id`; trả lại trong header `x-request-id` và `x-response-time-ms`.
- **Các metadata được ghi vào structured log:** trong handler `/chat` (`app/main.py`), `bind_contextvars` gắn `user_id_hash` (SHA-256 rút gọn qua `hash_user_id`), `session_id`, `feature`, `model` (lấy từ `agent.model`) và `env` trước log `request_received`; các contextvars này tự động merge vào mọi log sau đó trong cùng request nhờ processor `merge_contextvars`.
- **Cách bảo đảm PII được scrub trước khi ghi:** processor `scrub_event` (`app/logging_config.py`) được đăng ký ngay sau `TimeStamper` và trước `JsonlFileProcessor`/`JSONRenderer`, nên `payload` và `event` luôn được `scrub_text` (`app/pii.py`) xử lý trước khi serialize hoặc ghi file. Pattern có sẵn: email, điện thoại VN, CCCD, thẻ thanh toán.
- **Cách kiểm chứng kết quả:** chạy `python scripts/validate_logs.py` đạt 100/100 (`evidence/02-log-validator.png`); `python -m pytest -q` 24 passed (`evidence/01-pytest.png`), gồm test mới cho CCCD và thẻ thanh toán trong `tests/test_pii.py`; sample structured log đầy đủ metadata (`correlation_id=req-1a2b3c4d`) ở `evidence/04-structured-log.png`; gửi 1 message chứa cả 4 loại PII (`correlation_id=req-5e5e5e5e`) và xác nhận log output đã scrub hết trong `evidence/05-pii-redaction.png` — cùng trace của request này (`trace_id=2daaaa9db450a41429f91a67b42c3d9a`) cũng là trace dùng cho `evidence/08a-trace-metadata-root.png` và `evidence/08b-trace-metadata-generation.png`, đảm bảo `correlation_id` khớp giữa log và trace.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** dùng key `pk-lf-...`/`sk-lf-...` của project riêng `day13-k4-l3b-2A202602468` trong `.env`; `/health` trả `tracing_enabled: true`. Xác nhận qua Langfuse UI (`evidence/06-trace-list.png`, org "Nguyễn's Organization" / project `day13-k4-l3b-2A202602468`) và qua API `GET /api/public/v2/prompts` bằng chính key trong `.env` — 51 root trace (`lab-agent-run`, `isRootObservation=true`), vượt tối thiểu 10.
- **Cấu trúc root/retrieval/generation observations:** `LabAgent.run` (`app/agent.py`) là root observation (`@observe(name="lab-agent-run", as_type="agent")`); bên trong dùng `langfuse_client.start_as_current_observation(name="retrieval", as_type="retriever")` bọc `retrieve()` với output `doc_count`, và `start_as_current_observation(name="generation", as_type="generation")` bọc `FakeLLM.generate()` với `model`, `prompt` (managed prompt object), `usage_details` (`input`/`output` tokens) và `cost_details` (`total`). Root span vẫn giữ metadata `prompt_name/label/version/source`. Xem cây thật trong `evidence/07-trace-waterfall.png`; metadata root trong `evidence/08a-trace-metadata-root.png` và metadata generation (model/token/cost/prompt) trong `evidence/08b-trace-metadata-generation.png`.
- **Cách nối trace với log:** `correlation_id` được truyền vào `propagate_attributes(metadata={"correlation_id": correlation_id, ...})` ở root span, đồng thời cùng giá trị đó được bind vào structlog contextvars ở middleware, nên một `correlation_id` tra được cả trace lẫn các dòng log của cùng request. Bằng chứng đối chiếu: `correlation_id=req-1a2b3c4d` (`trace_id=2daaaa9db450a41429f91a67b42c3d9a`, dùng prompt version 2) xuất hiện đồng thời trong `evidence/04-structured-log.png` (log) và `evidence/08a-trace-metadata-root.png`/`08b-trace-metadata-generation.png` (trace).
- **Prompt name:** `day13-chat` (theo `LANGFUSE_PROMPT_NAME` trong `.env`).
- **Version/label baseline:** version 1, label `baseline` (ban đầu cũng gắn `production`) — xem `evidence/09-prompt-versions.png`.
- **Version/label candidate:** version 2, label `candidate` (nội dung prompt giữ nguyên 3 biến `{{feature}}`/`{{docs}}`/`{{message}}` theo `docs/PROMPT_VERSIONING.md`).
- **Trace ID của mỗi version:** cùng 1 query "How should alerts be designed?" (user `u10`/session `s10`) chạy với 2 label để so sánh:
  - version 1 (`label=baseline`): trace `a7069d0137c300b67119ed23d94e95e2`, `correlation_id=req-32c775e0`.
  - version 2 (`label=candidate`): trace `74e9c763468154b9d6b13f372629a6b6`, `correlation_id=req-61b45941`.
- **Cách promote và rollback `production`:** trên Langfuse UI, gắn label `production` sang version 2 (promote) — evidence `evidence/10a-prompt-production-v2.png` cho thấy version 2 đang mang `production`; sau đó gắn `production` trở lại version 1 (rollback) — evidence `evidence/10b-prompt-production-v1.png` cho thấy version 1 mang `production`/`baseline`, version 2 chỉ còn `latest`/`candidate`. App không cần sửa code khi đổi version — chỉ đọc theo `LANGFUSE_PROMPT_LABEL` trong `.env`. (Lưu ý: tại thời điểm chụp `08a/08b`, `production` đang trỏ version 2 nên trace đó cũng dùng version 2.)

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** contract 6 panel (latency/TTFT, traffic, errors + retrieval success, cost, tokens, quality) định nghĩa trong `config/dashboard.yaml`, `validate_dashboard.py` báo `6/6 panel`. Dashboard runtime dựng bằng script local `scripts/render_dashboard.py` (matplotlib, đọc trực tiếp `data/logs.jsonl` và tính đúng các phép tổng hợp trong `docs/DASHBOARD_SETUP.md`) — evidence `evidence/11-dashboard-overview.png`, có tên panel, đơn vị, time range/refresh và đường threshold/SLO cho từng panel.
- **SLO và lý do chọn:** `config/slo.yaml` — SLO `fast_successful_requests`: 99.5% request có `latency_ms <= 3000` trong cửa sổ 28 ngày. Giữ nguyên ngưỡng vì baseline load test cho thấy latency phần lớn ~400ms, chỉ request đầu batch có cold start retrieval lên ~2900ms, vẫn nằm dưới ngưỡng 3000ms của panel latency.
- **Cách tính error budget:** target 99.5% → error budget 0.5%. Với cửa sổ 28 ngày và giả định 10,000 request, error budget cho phép tối đa 50 request lỗi hoặc vượt latency 3000ms; vượt quá nghĩa là đã tiêu hết error budget và cần dừng thay đổi rủi ro (ví dụ promote prompt version mới) cho tới khi khắc phục.
- **Ba alert và runbook tương ứng:** định nghĩa trong `config/alert_rules.yaml`, runbook chi tiết trong `docs/alerts.md`:
  1. `HighLatencyP95` — `p95(latency_ms) > 3000ms` trong 5 phút, severity `warning`, runbook `docs/alerts.md#alert-1`.
  2. `LowRetrievalSuccessRate` — tỉ lệ `tool_success` (retrieval) `< 90%` trong 5 phút, severity `critical`, runbook `docs/alerts.md#alert-2`.
  3. `DailyCostBudgetExceeded` — `sum(cost_usd)` trong cửa sổ 60 phút `> 2.5 USD`, xác nhận lại sau 10 phút, severity `warning`, runbook `docs/alerts.md#alert-3`.
  Cả ba đều symptom-based, gắn kênh Slack `#k4-l3b-alerts` và owner `student-2A202602468`.

> Ví dụ cách viết error budget: "SLO 99.5% trong 28 ngày nghĩa là error budget 0.5%. Nếu workload có 10,000 request thì tối đa 50 request được phép lỗi hoặc chậm hơn ngưỡng SLO."

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1` (cohort K4, incident `rag_slow`, `latency_threshold_ms=2000`).
- **Khoảng thời gian điều tra:** `2026-09-30T04:44:28Z` – `04:44:44Z` (5 request `feature=monitoring` từ `scripts/load_test.py --challenge --concurrency 5`, sau khi bật incident bằng `scripts/inject_incident.py`).
- **Triệu chứng từ metrics:** Dashboard (`evidence/12-incident-metric.png`) cho thấy latency P95/P99 nhảy từ baseline ~152ms lên **~2653ms** (toàn bộ 5 request `monitoring`), trong khi `error_rate_pct=0` và `retrieval_success_pct=100%` — tức đây là triệu chứng **chậm thuần túy**, không phải lỗi.
- **Log line và correlation ID liên quan:** `correlation_id=req-b0aa0c8a` (`session_id=k4-l3b-challenge-s04`), `event=response_sent`, `latency_ms=2652`, `tool_success=true` — chi tiết đầy đủ và đối chiếu với 1 request bình thường (`req-713c51d2`, `latency_ms=151`) trong `evidence/13-incident-log.png`. 4 request còn lại của challenge (`req-0e99c904`, `req-70836efa`, `req-30a3d9ef`, `req-1abb65eb`) đều có `latency_ms` cùng khoảng ~2652–2654ms.
- **Trace ID và span gây ảnh hưởng:** `trace_id=5bd4ec5d497ba5e904fcb7d5b20fcbe5` (cùng `correlation_id=req-b0aa0c8a`, xác nhận qua Langfuse API `GET /api/public/v2/observations`) — span `retrieval` (type `RETRIEVER`) có latency **2.5s**, chiếm ~99% tổng thời gian trace (2.653s); span `generation` chỉ 0.151s, hoàn toàn bình thường.
- **Root cause:** Bước retrieval (RAG) trong `app/mock_rag.py::retrieve()` bị chậm bất thường (~2.5s) khi incident `rag_slow` được bật — khớp chính xác với `incident: "rag_slow"` khai báo trong `config/challenge.json`. Không phải lỗi ở LLM generation, không phải lỗi thực sự (retrieval vẫn trả `tool_success=true`), chỉ là latency tăng vọt ở đúng một bước.
- **Fix action:** Tắt incident bằng `python scripts/inject_incident.py --disable` (đã thực hiện, xác nhận `/health` trả `rag_slow: false`); trong hệ thống thật, hành động tương ứng là kiểm tra/khôi phục vector store hoặc dịch vụ retrieval đang chậm, thêm timeout cho bước retrieval để tránh kéo dài toàn bộ request.
- **Preventive measure:** Alert `HighLatencyP95` (`config/alert_rules.yaml`) dùng ngưỡng chung 3000ms nên **không bắt được** sự cố này (2653ms < 3000ms) dù đã vượt ngưỡng riêng của challenge (2000ms) — đây là khoảng trống cần ghi nhận: nên bổ sung một alert riêng theo dõi latency của span `retrieval` (không chỉ tổng latency request) với ngưỡng thấp hơn (ví dụ P95 retrieval > 1000ms), để phát hiện sớm sự cố `rag_slow` trước khi nó đẩy tổng latency lên gần ngưỡng SLO.

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Dùng đúng API `start_as_current_observation` của Langfuse SDK v4 để tạo child observation cho retrieval và generation, thay vì tự ghi log thủ công. Nhờ vậy waterfall lên đúng cây cha-con thật trên Langfuse, sau này CP3 mới khoanh vùng được span nào chậm thay vì chỉ đoán.
- **Một lỗi/blocker đã gặp:** Sau khi thêm child observation, test `test_agent_prompt_trace.py` báo lỗi `AttributeError: 'RecordingLangfuseClient' object has no attribute 'start_as_current_observation'`. Một blocker khác phát hiện muộn hơn: ảnh chụp metadata trace (`08a`, `08b`) vô tình để lộ `public_key` của Langfuse trong phần metadata mở rộng.
- **Cách tìm nguyên nhân và xử lý:** Với lỗi test, đọc traceback thấy mock client trong test cũ chỉ có `get_prompt`/`update_current_span`, chưa theo kịp API mới nên bổ sung thêm method giả lập tương ứng vào mock. Với ảnh lộ key, rà lại từng ảnh Langfuse trước khi commit theo đúng cảnh báo trong `RULES.md`, phát hiện dòng `scope.attributes.public_key` bị lọt vào khung hình rồi cắt ảnh bỏ phần đó trước khi đưa vào commit.
- **Cách hiểu luồng Metrics → Logs → Traces:** Dashboard cho thấy P95 latency nhảy từ ~152ms lên ~2653ms trong một khoảng thời gian cụ thể — đó là tín hiệu "có gì đó sai" nhưng chưa biết request nào. Lọc `data/logs.jsonl` theo `latency_ms` cao thì ra được `correlation_id` của request bất thường. Mở đúng trace có `correlation_id` đó mới thấy rõ span `retrieval` chiếm gần hết thời gian trong khi `generation` vẫn bình thường — kết luận root cause chỉ chắc chắn khi cả ba lớp cùng khớp nhau, không dừng ở một lớp.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Gắn `prompt_version`/`prompt_label` vào từng trace giúp biết chính xác một câu trả lời tệ hay latency tăng có phải do bản prompt mới hay không, và rollback chỉ là đổi label chứ không cần deploy lại code. Theo dõi `tokens_in/out` và `cost_usd` theo từng request giúp phát hiện chi phí tăng bất thường trước khi thành vấn đề tài chính. SLO/error budget biến "hệ thống ổn không" từ cảm tính thành một con số cụ thể để quyết định có nên tạm dừng thay đổi rủi ro hay không.
- **Điều quan trọng nhất đã học:** Một alert đặt ngưỡng theo cảm tính có thể không bắt được đúng sự cố thật — ngưỡng `HighLatencyP95 > 3000ms` không hề kích hoạt trong lúc incident `rag_slow` khiến latency lên tới 2653ms, vì ngưỡng đó vẫn còn cao hơn con số thực tế. Ngưỡng alert cần được kiểm chứng bằng dữ liệu incident thật, không chỉ suy đoán từ SLO tổng.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Dashboard runtime hiện là ảnh chụp một lần từ script local, chưa phải dashboard sống có thể theo dõi realtime. Ngưỡng của alert `HighLatencyP95` chưa được chỉnh lại dù đã phát hiện lỗ hổng ở trên.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.

## 10. Bonus

- **Cost optimization before/after (`scripts/compare_prompt_cost.py`):** so sánh cùng 10 query trong `data/sample_queries.jsonl` giữa template prompt hiện tại và một template rút gọn (chỉ đề xuất phân tích, không đổi `DEFAULT_PROMPT_TEMPLATE` thật vì đó là contract đã chấm ở CP2). Input token giảm ~10-12% mỗi request. Vì `FakeLLM` sinh `output_tokens` ngẫu nhiên (80-180) không phụ thuộc prompt và chi phí output ($15/1M) cao hơn input ($3/1M) nhiều lần, tổng cost chỉ giảm **0.6%** khi giữ cố định output_tokens=130 để cô lập đúng phần input — evidence `evidence/bonus-02-cost-optimization.png`. Ghi nhận trung thực: mock hiện tại không phản ánh đúng lợi ích thật của việc rút gọn prompt trên LLM thật.
- **Automation — secret/PII scan + CI (`scripts/scan_secrets.py`, `.github/workflows/ci.yml`):** script quét toàn bộ file text trong repo tìm pattern key Langfuse (`sk-lf-`/`pk-lf-`), token dạng Bearer, AWS key và cả 4 loại PII (dùng lại `app.pii.PII_PATTERNS`) — chính là loại lỗi thực tế đã gặp khi ảnh `08a/08b` lộ `public_key` trước khi commit. Kết quả sạch: `evidence/bonus-01-secret-scan.png`. CI (`.github/workflows/ci.yml`) tự động chạy quét secret, `pytest -q`, `load_test.py`, `validate_logs.py`, `validate_dashboard.py` trên mỗi lần push — tái hiện đúng checklist "Kiểm tra trước khi nộp" trong README, không cần Langfuse key (test cục bộ đã xác nhận app chạy đúng khi thiếu `.env`, `tracing_enabled=false`).
- **Audit log riêng (`app/audit_log.py`, `scripts/query_audit_log.py`):** log riêng biệt (`data/audit.jsonl`, không qua pipeline scrub/rotate của structlog) ghi lại hành động nhạy cảm — bật/tắt incident qua `/incidents/{name}/enable|disable`. Schema: `ts, action, target, result, correlation_id`. Retention: tài liệu hoá chính sách giữ 90 ngày (chưa tự động hoá rotate, ghi rõ trong docstring). Ví dụ truy vấn theo `action`/`target`/`result` trong `scripts/query_audit_log.py` — evidence `evidence/bonus-03-audit-log.png` cho thấy cả trường hợp thành công lẫn lỗi (`incident.enable` với tên incident không tồn tại) đều được ghi lại.

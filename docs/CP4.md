CP4 — Báo cáo, evidence và nộp bài
8.1. Báo cáo
Điền đủ mọi mục trong submission/REPORT.md (danh sách ở docs/SUBMISSION.md §8): thông tin, evidence index, bảng baseline và kết quả cuối, logging/PII, tracing/prompt (có 2 trace ID), dashboard/SLO/alert, điều tra challenge, quyết định kỹ thuật, blocker, bài học. Ảnh dẫn bằng đường dẫn tương đối, ví dụ ![Trace waterfall](evidence/07-trace-waterfall.png). Không dùng đường dẫn máy như C:\Users\....

8.2. Chụp evidence
Lưu ảnh .png (test/validator có thể dùng .txt) vào submission/evidence/.

Cách chụp:

Hệ điều hành	Phím tắt chụp một vùng
Windows	Win + Shift + S
macOS	Cmd + Shift + 4
Ubuntu	Shift + PrtSc
Quy tắc chung:

Ảnh phải thấy lệnh + kết quả (terminal), hoặc tên project + khoảng thời gian (Langfuse).
Chữ đọc được.
Không lộ .env, trang API Keys hay secret.
Để lấy log của một request, gửi request có ID tự đặt (req- + 8 ký tự hex) rồi in log của nó. Hai lệnh này dùng được trên mọi hệ điều hành; thay req-1a2b3c4d bằng ID của bạn:

python -c "import httpx; r = httpx.post('http://127.0.0.1:8000/chat', json={'user_id':'demo','session_id':'demo-01','feature':'qa','message':'Explain traces'}, headers={'x-request-id':'req-1a2b3c4d'}); print(r.status_code, r.headers.get('x-request-id'), r.headers.get('x-response-time-ms'))"
python -c "import json,sys; [print(json.dumps(json.loads(l), ensure_ascii=False, indent=2)) for l in open('data/logs.jsonl', encoding='utf-8') if sys.argv[1] in l]" req-1a2b3c4d
Chép
#	Tên file	Chụp ở đâu / làm gì	Ảnh phải thấy
01	01-pytest.png	Sau commit code cuối: git log -1 --oneline rồi python -m pytest -q	Mã commit + N passed
02	02-log-validator.png	Chuyển log cũ ra ngoài repo → restart → load_test.py → validate_logs.py	Khối Grading Scorecard + Estimated Score ≥ 80
03	03-dashboard-validator.png	python scripts/validate_dashboard.py	HỢP LỆ: 6/6 panel
04	04-structured-log.png	2 lệnh ở trên với ID tự đặt	2 khối JSON request_received + response_sent, đủ ts, event, correlation_id, user_id_hash, session_id, feature, model, env, latency_ms. Ghi ID vào report
05	05-pii-redaction.png	Như 04 nhưng message = a@b.vn 0901234567 001099012345 4111 1111 1111 1111 (câu ngắn vì preview bị cắt ở 80 ký tự)	Lệnh có PII và log hiện [REDACTED_EMAIL] [REDACTED_PHONE_VN] [REDACTED_CCCD] [REDACTED_CREDIT_CARD]
06	06-trace-list.png	Langfuse → Tracing	Tên project, khoảng thời gian, ≥ 10 trace day13-agent-request, cột Input/Output trống
07	07-trace-waterfall.png	Mở trace của request ở 04 → Timeline (bật Show labels) hoặc Tree	lab-agent-run là cha của retrieval và generation, mỗi dòng có thời gian
08	08a-…png, 08b-…png	08a: bấm lab-agent-run → Metadata. 08b: bấm generation	08a: correlation_id trùng ảnh 04, prompt_name/label/version, prompt_source=langfuse. 08b: model, token, cost, nhãn Prompt: day13-chat - vN. Input/Output trống
09	09-prompt-versions.png	Langfuse → Prompts → day13-chat	v1, v2 với nhãn baseline, candidate, production (có thêm latest là bình thường)
10	10a-…png, 10b-…png	Trang prompt sau khi promote (10a) và sau khi rollback (10b)	Nhãn production nằm ở v2 (10a), rồi quay về v1 (10b)
11	11-dashboard-overview.png (hoặc 11a/11b/11c)	Dashboard, chụp đủ 6 panel	Tên panel, đơn vị, threshold, time range; latency có TTFT; errors có retrieval success
12	12-incident-metric.png	Dashboard ngay sau challenge	Đoạn baseline và đoạn bất thường trên cùng trục thời gian
13	13-incident-log.png	Lọc request bất thường (lệnh bên dưới), rồi in 1 request bằng lệnh ở 04	Dòng log có correlation_id, giờ, giá trị bất thường
14	14-incident-trace.png	Langfuse, trace có cùng correlation_id với ảnh 13	Waterfall thấy span bất thường + metadata correlation_id
Lệnh lọc request bất thường cho ảnh 13:

# request chậm
python -c "import json; rows=[json.loads(l) for l in open('data/logs.jsonl', encoding='utf-8')]; [print(r['ts'], r['correlation_id'], r['session_id'], r['latency_ms'], 'ms') for r in rows if r.get('event')=='response_sent' and r.get('latency_ms',0)>2000]"
# request lỗi
python -c "import json; rows=[json.loads(l) for l in open('data/logs.jsonl', encoding='utf-8')]; [print(r['ts'], r['correlation_id'], r.get('session_id'), r.get('error_type'), r.get('tool_success')) for r in rows if r.get('event')=='request_failed']"
Chép
8.3. Tự kiểm tra chéo
Phải khớp	Giữa
Cùng correlation_id	04 ↔ 08a; 13 ↔ 14 ↔ phần incident trong report
Cùng trace	07, 08a, 08b là một trace, và trace đó có trong danh sách ở 06
Cùng thời điểm	Giờ trong log là UTC; Langfuse hiện giờ Việt Nam (+7 tiếng). Vd 04:39Z trong log = 11:39 trên Langfuse
Cùng version	2 trace ID trong report có prompt_version 1 và 2
Cùng người	Tên project day13-k4-l3b-<MSSV> trong ảnh khớp MSSV trong report và tên repo
Cùng đề	challenge_id trong report khớp đề đã tải
8.4. Kiểm tra cuối và nộp
python -m pytest -q
python scripts/validate_logs.py
python scripts/validate_dashboard.py
git status --short
git log -1 --oneline
Chép
Không dùng git add .. Chỉ add đúng phần bài làm, vd git add app tests config docs submission (cùng thư mục dashboard nếu có).
Kiểm tra git status không có .env, config/challenge.json, file log *.jsonl, .venv/.
Checklist:

submission/REPORT.md đủ mọi mục; ảnh dẫn bằng đường dẫn tương đối và mở được trên GitHub.
Có evidence 01–14; tests pass, log validator ≥ 80/100, dashboard validator 6/6.
≥ 10 trace trong project cá nhân; waterfall, metadata, prompt v1/v2, promote và rollback.
Dashboard đủ 6 panel; SLO/error budget có số cụ thể; 3 alert + runbook.
Incident đi theo Metrics → Logs → Traces, dùng cùng correlation_id.
Không có secret, PII thô, config/challenge.json, log, hay bài của người khác/lớp khác.
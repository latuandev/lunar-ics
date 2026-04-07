# Lunar ICS

`lunar-ics` là project Python để sinh và phục vụ dữ liệu lịch âm Việt Nam.

Project hỗ trợ:

- Tra cứu ngày dương sang âm lịch Việt Nam
- Tra cứu ngày âm sang dương lịch
- Lấy dữ liệu theo tháng, theo năm hoặc theo khoảng ngày
- Tải dataset dưới dạng JSON / CSV / ICS
- Subscribe lịch qua file `.ics`
- Chạy local hoặc bằng Docker + Docker Compose

## Phạm vi dữ liệu

- Dữ liệu hỗ trợ đầy đủ từ `2000-01-01` đến `2100-12-31`
- Timezone sử dụng cho logic lịch âm: `Asia/Ho_Chi_Minh`

Các file dữ liệu chính:

- `data/json/vn_lunar_2000_2100.json`
- `data/csv/vn_lunar_2000_2100.csv`
- `data/ics/vn_lunar_2000_2100.ics`
- `data/ics/vn_lunar_5y.ics`
- `data/json/year/{year}.json`
- `data/ics/year/{year}.ics`

## Feed subscription khuyến nghị

Feed mặc định để subscribe là:

- `/calendar/vn_lunar_5y.ics`

Feed này là **rolling 5 years**:

- Năm bắt đầu = năm hiện tại theo `Asia/Ho_Chi_Minh`
- Năm kết thúc = năm bắt đầu + 4

Ví dụ:

- nếu hiện tại ở Việt Nam là năm `2026` thì feed sẽ chứa `2026-01-01` đến `2030-12-31`
- nếu sang năm `2027` thì cùng URL đó sẽ tự chuyển thành `2027-01-01` đến `2031-12-31`

Lý do không nên dùng feed `2000–2100` làm subscription mặc định:

- File rất lớn
- Một số calendar client xử lý feed quá dài kém ổn định hơn
- Feed rolling 5 năm phù hợp hơn cho mục đích subscribe hàng ngày

## Các feed ICS hiện có

### Feed mặc định để subscribe

- `GET /calendar/vn_lunar_5y.ics`

### Feed theo năm

- `GET /calendar/year/{year}.ics`

Ví dụ:

- `/calendar/year/2026.ics`
- `/calendar/year/2030.ics`

### Feed toàn kỳ để tải về / archive / debug

- `GET /calendar/vn_lunar_2000_2100.ics`

Feed này vẫn được giữ lại, nhưng không còn là feed subscription được khuyến nghị.

## Chạy nhanh với Docker

Khởi động toàn bộ stack:

```bash
docker compose up --build -d
```

Kiểm tra nhanh:

```bash
curl http://127.0.0.1:${NGINX_HOST_PORT:-18080}/healthz
curl http://127.0.0.1:${NGINX_HOST_PORT:-18080}/api/v1/date/2024-02-10
curl -I http://127.0.0.1:${NGINX_HOST_PORT:-18080}/calendar/vn_lunar_5y.ics
```

Mặc định:

- App chạy nội bộ ở port `8000`
- Nginx publish ra host ở `127.0.0.1:18080`

## Chạy local

### Cài dependencies

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install -r requirements-dev.txt
```

### Build dataset

```bash
python3 -m app.main build-dataset --from-year 2000 --to-year 2100 --data-dir ./data
```

### Build riêng rolling feed

```bash
python3 -m app.main build-rolling-ics --years 5 --data-dir ./data
```

### Verify dataset

```bash
python3 -m app.main verify --from-year 2000 --to-year 2100 --data-dir ./data --load-existing
```

### Chạy server

```bash
python3 -m app.main serve --host 0.0.0.0 --port 8000 --data-dir ./data
```

### Smoke test

```bash
python3 -m app.main smoke-test --base-url http://127.0.0.1:8000
```

## Shortcut qua Makefile

```bash
make build-dataset
make verify
make serve
make smoke-test
make test
make lint
make typecheck
```

## API chính

Base path: `/api/v1`

### Health check

- `GET /healthz`

Ví dụ:

```bash
curl http://127.0.0.1:8000/healthz
```

### Dương lịch -> Âm lịch

- `GET /api/v1/date/YYYY-MM-DD`
- `GET /api/v1/solar-to-lunar?date=YYYY-MM-DD`

Ví dụ:

```bash
curl http://127.0.0.1:8000/api/v1/date/2024-02-10
curl "http://127.0.0.1:8000/api/v1/solar-to-lunar?date=2024-02-10"
```

### Âm lịch -> Dương lịch

- `GET /api/v1/lunar-to-solar?year=YYYY&month=MM&day=DD&leap=0|1`

Ví dụ:

```bash
curl "http://127.0.0.1:8000/api/v1/lunar-to-solar?year=2024&month=1&day=1&leap=0"
```

### Theo năm / tháng / khoảng ngày

- `GET /api/v1/year/{year}`
- `GET /api/v1/year/{year}?format=json|csv|ics`
- `GET /api/v1/month/{year}/{month}`
- `GET /api/v1/range?start=YYYY-MM-DD&end=YYYY-MM-DD`

Ví dụ:

```bash
curl http://127.0.0.1:8000/api/v1/year/2026
curl "http://127.0.0.1:8000/api/v1/year/2026?format=csv"
curl http://127.0.0.1:8000/api/v1/month/2026/2
curl "http://127.0.0.1:8000/api/v1/range?start=2026-02-01&end=2026-02-28"
```

### Metadata cho rolling feed

- `GET /api/v1/calendar/rolling-window`

Ví dụ:

```bash
curl http://127.0.0.1:8000/api/v1/calendar/rolling-window
```

### Calendar và download

- `GET /calendar/vn_lunar_5y.ics`
- `GET /calendar/year/{year}.ics`
- `GET /calendar/vn_lunar_2000_2100.ics`
- `GET /downloads/{path-under-data}`

Ví dụ:

```bash
curl -I http://127.0.0.1:8000/calendar/vn_lunar_5y.ics
curl -I http://127.0.0.1:8000/calendar/year/2026.ics
curl -I http://127.0.0.1:8000/calendar/vn_lunar_2000_2100.ics
curl http://127.0.0.1:8000/downloads/json/year/2026.json
```

## Subscribe trên Apple Calendar / iPhone / macOS

Nên dùng URL:

- `http://127.0.0.1:18080/calendar/vn_lunar_5y.ics`

Không nên dùng feed `2000–2100` làm subscription mặc định vì file lớn hơn cần thiết cho phần lớn client.

Feed theo năm cũng có sẵn nếu bạn chỉ muốn một năm cụ thể:

- `http://127.0.0.1:18080/calendar/year/2026.ics`

## Reverse proxy từ Nginx trên host

Nginx container đã publish ra host port `18080` mặc định, nên Nginx trên host chỉ cần proxy tới địa chỉ này.

Ví dụ:

```nginx
location /lunar/ {
    proxy_pass http://127.0.0.1:18080/;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## CLI có sẵn

```bash
python -m app.main build-dataset --from-year 2000 --to-year 2100
python -m app.main build-rolling-ics --years 5
python -m app.main verify --from-year 2000 --to-year 2100
python -m app.main serve
python -m app.main smoke-test
```

Wrapper scripts:

```bash
python3 scripts/build_dataset.py
python3 scripts/verify_dataset.py
python3 scripts/smoke_test.py
```

## Test và kiểm tra chất lượng

```bash
pytest -q
ruff check app tests
mypy app
```

## Biến môi trường thường dùng

- `APP_HOST`
- `APP_PORT`
- `DATA_DIR`
- `NGINX_HOST_PORT`
- `TZ`
- `LOG_LEVEL`
- `STATIC_CACHE_SECONDS`

Ví dụ:

```bash
APP_PORT=8000 DATA_DIR=./data python3 -m app.main serve
NGINX_HOST_PORT=18080 docker compose up --build -d
```

## Troubleshooting

### Chưa có dataset

```bash
python3 -m app.main build-dataset --from-year 2000 --to-year 2100 --data-dir ./data
python3 -m app.main build-rolling-ics --years 5 --data-dir ./data
```

### API trả `invalid_input`

Kiểm tra lại:

- Date có đúng định dạng `YYYY-MM-DD`
- `month` nằm trong `1..12`
- `day` nằm trong `1..30` đối với input âm
- `leap` chỉ nhận `0` hoặc `1`

### Docker chạy nhưng host không truy cập được

Kiểm tra:

```bash
docker compose ps
curl http://127.0.0.1:${NGINX_HOST_PORT:-18080}/healthz
```

## Ghi chú

- Project không dùng database server.
- Dữ liệu được build sẵn và phục vụ trực tiếp từ file.
- Feed subscription mặc định hiện tại là rolling 5 years, không còn là feed toàn kỳ `2000–2100`.

## Author

- Name: Tuan Le
- Website: <https://atun29.devnook.net>
- Email: <mailto:latuan.dev@gmail.com>

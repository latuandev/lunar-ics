# Lunar ICS

`lunar-ics` là project Python để sinh và phục vụ dữ liệu lịch âm Việt Nam cho dải ngày từ `2000-01-01` đến `2100-12-31`.

Project này phù hợp cho các nhu cầu:

- Tra cứu ngày dương sang âm lịch Việt Nam
- Tra cứu ngày âm sang dương lịch
- Lấy dữ liệu theo tháng, theo năm hoặc theo khoảng ngày
- Tải dataset đã sinh sẵn dưới dạng JSON / CSV / ICS
- Subscribe file `.ics` như một external calendar
- Chạy local hoặc bằng Docker + Docker Compose

## Phạm vi dữ liệu

- Hỗ trợ đầy đủ từ `2000-01-01` đến `2100-12-31`
- Timezone sử dụng cho logic lịch âm: `Asia/Ho_Chi_Minh`

Các file dữ liệu chính:

- `data/json/vn_lunar_2000_2100.json`
- `data/csv/vn_lunar_2000_2100.csv`
- `data/ics/vn_lunar_2000_2100.ics`
- `data/json/year/{year}.json`
- `data/ics/year/{year}.ics`

## Chạy nhanh với Docker

Khởi động toàn bộ stack:

```bash
docker compose up --build -d
```

Kiểm tra nhanh:

```bash
curl http://127.0.0.1:${NGINX_HOST_PORT:-18080}/healthz
curl http://127.0.0.1:${NGINX_HOST_PORT:-18080}/api/v1/date/2024-02-10
curl -I http://127.0.0.1:${NGINX_HOST_PORT:-18080}/calendar/vn_lunar_2000_2100.ics
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
curl http://127.0.0.1:8000/api/v1/year/2024
curl "http://127.0.0.1:8000/api/v1/year/2024?format=csv"
curl http://127.0.0.1:8000/api/v1/month/2024/2
curl "http://127.0.0.1:8000/api/v1/range?start=2024-02-01&end=2024-02-29"
```

### Calendar và download

- `GET /calendar/vn_lunar_2000_2100.ics`
- `GET /calendar/year/{year}.ics`
- `GET /downloads/{path-under-data}`

Ví dụ:

```bash
curl -I http://127.0.0.1:8000/calendar/vn_lunar_2000_2100.ics
curl http://127.0.0.1:8000/downloads/json/year/2024.json
```

## ICS subscription

Bạn có thể dùng file ICS tổng hoặc ICS theo năm để subscribe từ các calendar client phổ biến.

Ví dụ URL:

- `http://127.0.0.1:18080/calendar/vn_lunar_2000_2100.ics`
- `http://127.0.0.1:18080/calendar/year/2024.ics`

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

- `APP_PORT`
- `NGINX_HOST_PORT`
- `DATA_DIR`
- `TZ`
- `LOG_LEVEL`

Ví dụ:

```bash
APP_PORT=8000 DATA_DIR=./data python3 -m app.main serve
NGINX_HOST_PORT=18080 docker compose up --build -d
```

## Troubleshooting

### Chưa có dataset

```bash
python3 -m app.main build-dataset --from-year 2000 --to-year 2100 --data-dir ./data
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

## Author

- Name: Tuan Le
- Website: [https://atun29.devnook.net](https://atun29.devnook.net)
- Email: latuan.dev@gmail.com

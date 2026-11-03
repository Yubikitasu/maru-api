# osu! API

Backend API cho Maru Overlay, được xây dựng bằng [FastAPI](https://fastapi.tiangolo.com/). Project cung cấp dữ liệu người chơi, best scores, leaderboard beatmap và màu chủ đạo từ avatar osu! Hệ thống hỗ trợ cả osu! Bancho và Akatsuki.

## Tính năng

- Lấy thông tin người chơi theo mode `osu` hoặc `mania`.
- Lấy best scores của người chơi.
- Lấy leaderboard của beatmap.
- Lấy màu chủ đạo từ avatar người chơi.
- Chuyển đổi giữa server osu! Bancho và Akatsuki.
- Tài liệu API tự động qua Swagger UI và ReDoc.
- Hỗ trợ chạy local và deploy trên Vercel.

## Công nghệ

- Python 3.10+
- FastAPI
- Uvicorn
- HTTPX
- python-dotenv
- ColorThief

## Cài đặt

### 1. Clone project

```bash
git clone https://github.com/Yubikitasu/maru-api.git
cd osuAPI
```

Nếu tên thư mục sau khi clone khác `osuAPI`, hãy dùng đúng tên thư mục đó trong lệnh `cd`.

### 2. Tạo virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Cài dependencies

```bash
pip install -r requirements.txt
```

### 4. Cấu hình biến môi trường

Tạo file `.env` ở thư mục gốc:

```env
OSU_API_KEY=your_osu_api_v1_key
FRONTEND_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

`OSU_API_KEY` được dùng khi gọi osu! API v1 cho dữ liệu Bancho. `FRONTEND_ORIGINS` là danh sách origin được phép gọi API, phân tách bằng dấu phẩy. Hai origin local của Maru Overlay tại port `24050` đã được cấu hình sẵn.

Không đưa `.env` hoặc API key lên GitHub.

## Chạy local

```bash
python run.py
```

Server mặc định chạy tại:

```text
http://127.0.0.1:8000
```

Tài liệu API:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## API endpoints

### Health check

```http
GET /
```

### User

```http
GET /users/{username}/{gameMode}
GET /users/{user_id}/best/{gameMode}
```

`gameMode` hiện hỗ trợ `osu` và `mania`.

Ví dụ:

```text
GET /users/123456/osu
GET /users/123456/mania
GET /users/123456/mania?server=akatsuki
GET /users/123456/best/osu
```

### Beatmap leaderboard

```http
GET /beatmaps/{beatmap_id}/{mode}
```

Ví dụ:

```text
GET /beatmaps/12059810/osu
GET /beatmaps/12059810/mania
GET /beatmaps/12059810/osu?server=akatsuki
GET /beatmaps/12059810/osu?server=akatsuki&server_mods=relax
```

Khi dùng Akatsuki, `server_mods` có thể là `relax` hoặc `autopilot`.

### Màu avatar

```http
GET /color/{user_id}
```

Ví dụ:

```text
GET /color/123456
GET /color/123456?server=akatsuki
```

### User preferences

Endpoint mẫu để nhận preference:

```http
POST /users/{user_id}/preferences
Content-Type: application/json
```

Request body:

```json
{
	"favorite_mode": 0
}
```

## Deploy trên Vercel

Project đã có sẵn `vercel.json` và entry point `api/index.py`.

### Deploy bằng Vercel CLI

```bash
npm install -g vercel
vercel login
vercel
```

Sau khi project đã được liên kết với Vercel, thêm biến môi trường:

```bash
vercel env add OSU_API_KEY
vercel env add FRONTEND_ORIGINS
```

Deploy production:

```bash
vercel --prod
```

Bạn cũng có thể import repository GitHub trực tiếp trong Vercel Dashboard, sau đó thêm `OSU_API_KEY` và `FRONTEND_ORIGINS` tại **Project Settings > Environment Variables**.

## Cấu trúc project

```text
.
├── api/
│   └── index.py          # Entry point cho Vercel
├── routers/
│   ├── beatmaps.py       # Beatmap endpoints
│   ├── color.py          # Avatar color endpoint
│   ├── users.py          # User endpoints
│   └── helpers/          # Tích hợp Bancho và Akatsuki
├── main.py               # Khởi tạo FastAPI app
├── run.py                # Chạy server local
├── requirements.txt      # Python dependencies
└── vercel.json           # Cấu hình Vercel
```

## Nguồn dữ liệu

API sử dụng dữ liệu và avatar từ các dịch vụ osu! Bancho, Akatsuki và các CDN liên quan. Việc sử dụng dữ liệu cần tuân thủ điều khoản của từng dịch vụ.
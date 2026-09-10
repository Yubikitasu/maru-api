# osu! API

API nhỏ xây dựng bằng FastAPI để lấy thông tin người chơi, best scores, leaderboard beatmap và màu chủ đạo từ avatar osu! Hỗ trợ dữ liệu từ osu! Bancho và Akatsuki.

## Yêu cầu

- Python 3.10+
- `pip`
- osu! API v1 key cho các endpoint Bancho

## Cài đặt

```bash
git clone <URL_REPOSITORY>
cd osuAPI
python -m venv .venv
```

Kích hoạt môi trường ảo:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS/Linux
source .venv/bin/activate
```

Cài dependencies:

```bash
pip install -r requirements.txt
```

Tạo file `.env` ở thư mục gốc:

```env
OSU_API_KEY=your_osu_api_v1_key
FRONTEND_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Không commit file `.env` lên GitHub.

## Chạy local

```bash
python run.py
```

API chạy tại `http://127.0.0.1:8000`. Tài liệu tương tác:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoint chính

| Method | Endpoint | Mô tả |
| --- | --- | --- |
| `GET` | `/` | Kiểm tra API |
| `GET` | `/users/{username}/{gameMode}` | Thông tin user; `gameMode`: `osu` hoặc `mania` |
| `GET` | `/users/{user_id}/best/{gameMode}` | 5 best scores của user |
| `POST` | `/users/{user_id}/preferences` | Lưu preference mẫu |
| `GET` | `/beatmaps/{beatmap_id}/{mode}` | Leaderboard beatmap |
| `GET` | `/color/{user_id}` | Màu chủ đạo từ avatar user |

Thêm `?server=akatsuki` để dùng Akatsuki. Với Akatsuki, có thể dùng thêm `server_mods=relax` hoặc `server_mods=autopilot`.

Ví dụ:

```text
GET /users/123456/osu
GET /users/123456/mania?server=akatsuki
GET /users/123456/best/osu
GET /beatmaps/12059810/mania
GET /beatmaps/12059810/osu?server=akatsuki&server_mods=relax
GET /color/123456
```

## Deploy lên Vercel

Project đã có `vercel.json` và entry point tại `api/index.py`.

```bash
npm install -g vercel
vercel login
vercel
vercel env add OSU_API_KEY
vercel env add FRONTEND_ORIGINS
vercel --prod
```

Hoặc import repository từ GitHub vào Vercel rồi thêm các biến môi trường trong phần Project Settings.

## Giấy phép và nguồn dữ liệu

Project sử dụng dữ liệu từ osu! Bancho API, Akatsuki API và avatar CDN tương ứng. Hãy tuân thủ điều khoản sử dụng của các dịch vụ này.
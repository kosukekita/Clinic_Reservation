from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine
from .routers import auth, slots, reservations

# データベースのテーブルを作成
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="クリニック予約システム API")

# CORSミドルウェア設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に設定してください
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターを登録
app.include_router(auth.router, tags=["Authentication"])
app.include_router(slots.router, tags=["Time Slots"])
app.include_router(reservations.router, tags=["Reservations"])


@app.get("/")
def read_root():
    return {"message": "Welcome to Clinic Reservation System API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
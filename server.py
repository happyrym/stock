from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import sqlite3

from crawler import get_stock_price
import firebase_admin
from firebase_admin import credentials, messaging

# Firebase 초기화
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)

app = FastAPI()

DB_NAME = "stocks.db"

# DB 초기화
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registered_stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_token TEXT NOT NULL,
            stock_code TEXT NOT NULL,
            target_price REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Request Body 모델
class StockRegister(BaseModel):
    device_token: str
    stock_code: str
    target_price: float

class StockUnregister(BaseModel):
    device_token: str
    stock_code: str

# 종목 등록 API
@app.post("/register_stock")
def register_stock(item: StockRegister):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO registered_stocks (device_token, stock_code, target_price)
        VALUES (?, ?, ?)
    ''', (item.device_token, item.stock_code, item.target_price))
    conn.commit()
    conn.close()
    return {"message": "Stock registered successfully"}

# 종목 삭제 API
@app.post("/unregister_stock")
def unregister_stock(item: StockUnregister):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM registered_stocks
        WHERE device_token = ? AND stock_code = ?
    ''', (item.device_token, item.stock_code))
    conn.commit()
    conn.close()
    return {"message": "Stock unregistered successfully"}

# 등록된 종목 리스트 조회 API
@app.get("/list_stocks")
def list_stocks():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, device_token, stock_code, target_price FROM registered_stocks')
    rows = cursor.fetchall()
    conn.close()
    return {"stocks": rows}

def send_fcm_push(device_token, title, body):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        token=device_token
    )
    response = messaging.send(message)
    print(f"[INFO] Successfully sent message: {response}")

# if __name__ == "__main__":
#     test_code = "005930"  # 삼성전자
#     price = get_stock_price(test_code)
#     print(f"{test_code} 현재가: {price}")
import schedule
import time
import threading

def job_check_prices():
    print("[INFO] Checking stock prices...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, device_token, stock_code, target_price FROM registered_stocks')
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        id, device_token, stock_code, target_price = row
        current_price = get_stock_price(stock_code)
        if current_price is None:
            continue

        print(f"[DEBUG] {stock_code} 현재가: {current_price} / 목표가: {target_price}")

        if current_price >= target_price:
            title = f"{stock_code} 목표가 달성!"
            body = f"현재가 {current_price}원이 목표가 {target_price}원을 돌파했습니다."
            send_fcm_push(device_token, title, body)

            # 목표 달성 후 DB에서 삭제 (선택사항)
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM registered_stocks WHERE id = ?', (id,))
            conn.commit()
            conn.close()
            print(f"[INFO] {stock_code} 알림 후 DB에서 삭제 완료.")

def run_scheduler():
    schedule.every(5).minutes.do(job_check_prices)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # 테스트용 단독 실행
    test_code = "005930"
    price = get_stock_price(test_code)
    print(f"{test_code} 현재가: {price}")

    # 스케줄러 실행
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # uvicorn 서버 실행
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

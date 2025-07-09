from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import sqlite3

from crawler import get_stock_price

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

# if __name__ == "__main__":
#     test_code = "005930"  # 삼성전자
#     price = get_stock_price(test_code)
#     print(f"{test_code} 현재가: {price}")

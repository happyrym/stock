import requests
from bs4 import BeautifulSoup


def get_stock_price(stock_code):
    """
    네이버 금융에서 주식 현재가 크롤링
    :param stock_code: 종목 코드 (예: '005930')
    :return: 현재가 (int) 또는 None
    """
    try:
        url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        price_tag = soup.select_one("p.no_today span.blind")
        if price_tag:
            price_text = price_tag.get_text().replace(",", "")
            return int(price_text)
        else:
            print(f"[WARN] 가격 정보를 찾을 수 없습니다: {stock_code}")
            return None
    except Exception as e:
        print(f"[ERROR] 크롤링 실패: {e}")
        return None

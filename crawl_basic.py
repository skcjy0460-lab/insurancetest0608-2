import requests
from bs4 import BeautifulSoup
import time

# ── 1단계: 웹페이지 HTML 가져오기 ──────────────────────────
url = "https://www.hira.or.kr/bbsDummy.do?pgmid=HIRAA020002000100"

headers = {
    # 브라우저처럼 보이게 위장 (없으면 차단당할 수 있음)
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

response = requests.get(url, headers=headers)
response.encoding = "utf-8"

print("상태코드:", response.status_code)  # 200이면 성공
print("HTML 일부:", response.text[:500])  # 앞부분 미리보기


# ── 2단계: HTML에서 원하는 부분만 추출 ────────────────────
soup = BeautifulSoup(response.text, "html.parser")

# 예: 게시글 제목들 가져오기
# (실제 사이트마다 태그 구조가 다름 → 개발자도구로 확인 필요)
titles = soup.select("td.title a")  # CSS 선택자로 제목 링크 찾기

for title in titles:
    print("제목:", title.text.strip())
    print("링크:", title.get("href"))
    print("---")


# ── 3단계: 여러 페이지 반복 수집 ──────────────────────────
results = []

for page in range(1, 6):  # 1~5페이지
    url = f"https://www.hira.or.kr/bbsDummy.do?pgmid=HIRAA020002000100&page={page}"
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    rows = soup.select("table.board_list tbody tr")
    
    for row in rows:
        cols = row.select("td")
        if len(cols) >= 3:
            results.append({
                "번호": cols[0].text.strip(),
                "제목": cols[1].text.strip(),
                "날짜": cols[2].text.strip(),
            })
    
    time.sleep(1)  # 1초 대기 (서버 부하 방지 - 예의 바른 크롤링)
    print(f"{page}페이지 완료")

print(f"\n총 {len(results)}건 수집")
for r in results[:3]:  # 처음 3개만 출력
    print(r)

"""
심평원 + 보건복지부 고시 크롤러
- 고시 목록 수집
- 신규 고시 감지
- SQLite DB 저장
"""
import requests
from bs4 import BeautifulSoup
import sqlite3
import time
from datetime import datetime

# ── DB 초기화 ──────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("hira_notices.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            source      TEXT,        -- 출처 (심평원/보건복지부)
            title       TEXT,        -- 제목
            date        TEXT,        -- 고시일
            url         TEXT UNIQUE, -- 원문 링크 (중복방지)
            content     TEXT,        -- 본문 내용
            created_at  TEXT         -- 수집일시
        )
    """)
    conn.commit()
    return conn


# ── 보건복지부 고시 목록 크롤링 ───────────────────────────
def crawl_mohw(conn, pages=3):
    """보건복지부 훈령/예규/고시 목록 수집"""
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    new_count = 0
    
    for page in range(1, pages + 1):
        url = (
            "https://www.mohw.go.kr/board.es"
            f"?mid=a10409020000&bid=0026&page={page}"
        )
        
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = "utf-8"
            soup = BeautifulSoup(res.text, "html.parser")
            
            # 게시글 목록 파싱 (실제 태그는 개발자도구로 확인)
            rows = soup.select("table tbody tr")
            
            for row in rows:
                cols = row.select("td")
                if len(cols) < 3:
                    continue
                
                title_tag = row.select_one("td a")
                if not title_tag:
                    continue
                
                title = title_tag.text.strip()
                href  = title_tag.get("href", "")
                date  = cols[-1].text.strip()
                full_url = "https://www.mohw.go.kr" + href if href.startswith("/") else href
                
                # 급여기준 관련 고시만 필터링
                keywords = ["급여기준", "요양급여", "보험인정", "약제급여", "행위급여"]
                if not any(kw in title for kw in keywords):
                    continue
                
                # DB에 없는 것만 저장 (url이 UNIQUE)
                try:
                    conn.execute("""
                        INSERT INTO notices (source, title, date, url, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, ("보건복지부", title, date, full_url, datetime.now().isoformat()))
                    conn.commit()
                    new_count += 1
                    print(f"  [신규] {title[:50]}...")
                except sqlite3.IntegrityError:
                    pass  # 이미 있는 항목 → 스킵
            
            time.sleep(1)  # 서버 부하 방지
            print(f"보건복지부 {page}페이지 완료")
            
        except Exception as e:
            print(f"오류 발생: {e}")
    
    return new_count


# ── 심평원 공지사항 크롤링 ────────────────────────────────
def crawl_hira(conn, pages=3):
    """심평원 공지사항·고시 목록 수집"""
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    new_count = 0
    
    for page in range(1, pages + 1):
        url = (
            "https://www.hira.or.kr/bbsDummy.do"
            f"?pgmid=HIRAA020002000100&page={page}"
        )
        
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = "utf-8"
            soup = BeautifulSoup(res.text, "html.parser")
            
            rows = soup.select("table tbody tr")
            
            for row in rows:
                title_tag = row.select_one("td a")
                if not title_tag:
                    continue
                
                title    = title_tag.text.strip()
                href     = title_tag.get("href", "")
                date_td  = row.select("td")
                date     = date_td[-1].text.strip() if date_td else ""
                full_url = "https://www.hira.or.kr" + href if href.startswith("/") else href
                
                try:
                    conn.execute("""
                        INSERT INTO notices (source, title, date, url, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, ("심평원", title, date, full_url, datetime.now().isoformat()))
                    conn.commit()
                    new_count += 1
                    print(f"  [신규] {title[:50]}...")
                except sqlite3.IntegrityError:
                    pass
            
            time.sleep(1)
            print(f"심평원 {page}페이지 완료")
            
        except Exception as e:
            print(f"오류: {e}")
    
    return new_count


# ── 메인 실행 ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("급여기준 고시 크롤러 시작")
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 50)
    
    conn = init_db()
    
    print("\n[1] 보건복지부 고시 수집 중...")
    n1 = crawl_mohw(conn, pages=3)
    
    print("\n[2] 심평원 공지 수집 중...")
    n2 = crawl_hira(conn, pages=3)
    
    total = n1 + n2
    print(f"\n완료! 신규 수집: {total}건")
    
    # 수집 결과 확인
    rows = conn.execute(
        "SELECT source, title, date FROM notices ORDER BY date DESC LIMIT 10"
    ).fetchall()
    
    print("\n최근 수집 10건:")
    for r in rows:
        print(f"  [{r[0]}] {r[2]} | {r[1][:40]}")
    
    conn.close()

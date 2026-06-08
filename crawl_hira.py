"""
심평원 + 보건복지부 고시 크롤러
- 매일 GitHub Actions에서 자동 실행
- 수집 결과를 Supabase DB에 저장
"""
import requests
from bs4 import BeautifulSoup
import time
import os
from datetime import datetime
from supabase import create_client

# ── Supabase 연결 ──────────────────────────────────────────
def get_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise Exception("SUPABASE_URL, SUPABASE_KEY 환경변수를 설정해주세요")
    return create_client(url, key)


# ── 보건복지부 고시 크롤링 ────────────────────────────────
def crawl_mohw(supabase, pages=3):
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

            rows = soup.select("table tbody tr")
            for row in rows:
                title_tag = row.select_one("td a")
                if not title_tag:
                    continue

                title = title_tag.text.strip()
                href  = title_tag.get("href", "")
                tds   = row.select("td")
                date  = tds[-1].text.strip() if tds else ""
                full_url = "https://www.mohw.go.kr" + href if href.startswith("/") else href

                # 급여기준 관련만 필터링
                keywords = ["급여기준", "요양급여", "보험인정", "약제급여", "행위급여", "요양급여적용기준"]
                if not any(kw in title for kw in keywords):
                    continue

                # Supabase에 저장 (url 중복 시 무시)
                try:
                    supabase.table("notices").upsert({
                        "source": "보건복지부",
                        "title": title,
                        "date": date,
                        "url": full_url,
                        "created_at": datetime.now().isoformat(),
                    }, on_conflict="url").execute()
                    new_count += 1
                    print(f"  [저장] {title[:50]}")
                except Exception as e:
                    print(f"  [스킵] {e}")

            time.sleep(1)
            print(f"보건복지부 {page}페이지 완료")

        except Exception as e:
            print(f"오류: {e}")

    return new_count


# ── 심평원 공지 크롤링 ────────────────────────────────────
def crawl_hira(supabase, pages=3):
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
                tds      = row.select("td")
                date     = tds[-1].text.strip() if tds else ""
                full_url = "https://www.hira.or.kr" + href if href.startswith("/") else href

                try:
                    supabase.table("notices").upsert({
                        "source": "심평원",
                        "title": title,
                        "date": date,
                        "url": full_url,
                        "created_at": datetime.now().isoformat(),
                    }, on_conflict="url").execute()
                    new_count += 1
                    print(f"  [저장] {title[:50]}")
                except Exception as e:
                    print(f"  [스킵] {e}")

            time.sleep(1)
            print(f"심평원 {page}페이지 완료")

        except Exception as e:
            print(f"오류: {e}")

    return new_count


# ── 메인 ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print(f"크롤러 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    supabase = get_supabase()

    print("\n[1] 보건복지부 수집 중...")
    n1 = crawl_mohw(supabase, pages=3)

    print("\n[2] 심평원 수집 중...")
    n2 = crawl_hira(supabase, pages=3)

    print(f"\n완료! 총 신규 {n1 + n2}건 저장")

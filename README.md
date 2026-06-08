# 🏥 MEDIUM - 급여기준 및 최신고시 (Streamlit 버전)

AI가 심평원(hira.or.kr)을 실시간 검색하여 최신 급여기준을 안내합니다.

---

## 🚀 배포 방법

### 1단계: GitHub에 올리기

```bash
# 터미널에서 이 폴더 안에서 실행
git init
git add .
git commit -m "첫 커밋"

# GitHub에서 새 저장소 만든 후
git remote add origin https://github.com/본인아이디/hira-search.git
git branch -M main
git push -u origin main
```

### 2단계: Streamlit Cloud 연결

1. [share.streamlit.io](https://share.streamlit.io) 접속
2. GitHub 계정으로 로그인
3. **"New app"** 클릭
4. Repository 선택 → Main file: `app.py` → **Deploy**

### 3단계: API 키 설정 ⚠️ 필수

Streamlit Cloud 대시보드 → 앱 설정 → **Secrets** 탭에 아래 내용 입력:

```toml
ANTHROPIC_API_KEY = "sk-ant-api03-여기에-실제-키-입력"
```

저장 후 앱이 자동으로 재시작됩니다.

---

## 💻 로컬 실행 방법

```bash
# 패키지 설치
pip install -r requirements.txt

# .env 파일 생성
cp .env.example .env
# .env 파일을 열어서 실제 API 키 입력

# 앱 실행
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 열기

---

## 🔑 Anthropic API 키 발급

1. [console.anthropic.com](https://console.anthropic.com) 접속
2. 로그인 → **API Keys** 메뉴
3. **Create Key** → 키 복사

---

## 📁 파일 구조

```
hira-streamlit/
├── app.py              # 메인 Streamlit 앱
├── requirements.txt    # 필요 패키지
├── .gitignore          # .env 등 제외 목록
├── .env.example        # 환경변수 예시 (참고용)
└── README.md
```

---

## ⚠️ 주의사항

- `.env` 파일은 절대 GitHub에 올리지 마세요 (`.gitignore`에 포함됨)
- API 키는 Streamlit Cloud의 **Secrets**에만 저장하세요
- Anthropic API 사용 비용 발생 (검색 1회당 약 $0.01~0.03)
- AI 결과는 참고용이며, 실제 청구 전 심평원 공식 고시를 확인하세요

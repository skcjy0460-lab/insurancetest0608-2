import streamlit as st
import anthropic
import os

# ── 페이지 설정 ──────────────────────────────────────────
st.set_page_config(
    page_title="MEDIUM - 급여기준 및 최신고시",
    page_icon="🏥",
    layout="wide",
)

# ── CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f5f7f9; }
    .stButton>button {
        background-color: #0d7a6b; color: white;
        border-radius: 8px; border: none;
        font-weight: 700; padding: 8px 20px;
    }
    .stButton>button:hover { background-color: #0a9e87; }
    .tag-btn>button {
        background-color: white !important; color: #0d7a6b !important;
        border: 1px solid #b2ddd8 !important; border-radius: 20px !important;
        font-size: 12px !important; padding: 4px 12px !important;
    }
    .result-box {
        background: #f8fffe; border: 1px solid #d4ede9;
        border-radius: 12px; padding: 16px; margin: 8px 0;
    }
    .result-header {
        background: #e8f7f5; border-radius: 8px 8px 0 0;
        padding: 8px 14px; font-size: 12px;
        color: #0d7a6b; font-weight: 700; margin-bottom: 10px;
    }
    .user-msg {
        background: #0d7a6b; color: white;
        border-radius: 12px 12px 2px 12px;
        padding: 10px 14px; margin: 8px 0;
        display: inline-block; max-width: 80%; float: right; clear: both;
    }
    .badge-live {
        background: #e8f7f5; color: #0d7a6b;
        border: 1px solid #b2ddd8; border-radius: 20px;
        padding: 3px 10px; font-size: 11px; font-weight: 700;
    }
    .source-link { font-size: 12px; color: #0066cc; }
</style>
""", unsafe_allow_html=True)

# ── API 키 로드 ──────────────────────────────────────────
# Streamlit Cloud → Secrets에서 가져오기
# 로컬 → .env 파일 또는 직접 입력
def get_api_key():
    # 1순위: Streamlit Secrets (배포 환경)
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass
    # 2순위: 환경변수 (로컬 .env)
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        return key
    # 3순위: 세션에 저장된 키
    return st.session_state.get("api_key", "")

# ── 시스템 프롬프트 ───────────────────────────────────────
SYSTEM_PROMPT = """당신은 한국 건강보험심사평가원(심평원)의 급여기준 및 최신고시 전문 AI 어시스턴트입니다.

웹 검색 도구(web_search)를 반드시 사용하여 심평원(hira.or.kr) 최신 정보를 검색한 후 답변하세요.

검색 전략:
1. "site:hira.or.kr [검색어] 급여기준" 으로 심평원 공식 사이트 검색
2. "심평원 [검색어] 고시 인정기준 2024 OR 2025" 로 최신 정보 검색

답변 형식:
**🔍 검색된 급여기준**
[핵심 인정기준 요약]

**✅ 인정 조건**
[상병, 투여 기준, 용량, 적응증 등]

**⚠️ 청구 시 주의사항**
[심사 시 자주 지적되는 사항]

**📋 관련 고시**
[고시번호, 시행일]

**🔗 출처**
[참조한 심평원 페이지 URL]

중요: 반드시 web_search 도구로 실시간 검색 후 답변하세요."""

# ── 세션 초기화 ───────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "checks" not in st.session_state:
    st.session_state.checks = {
        "최신 고시 변경 여부 확인": False,
        "의무기록 보완 필요 항목 확인": False,
        "청구 전 누락 가능성 점검": False,
    }

# ── AI 검색 함수 ──────────────────────────────────────────
def search_hira(query: str, api_key: str):
    client = anthropic.Anthropic(api_key=api_key)
    history = [{"role": m["role"], "content": m["content"]}
               for m in st.session_state.messages]
    history.append({"role": "user", "content": query})

    # 1차 호출 (웹 검색 도구 포함)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=history,
    )

    full_text = ""
    blocks = response.content

    # 웹 검색이 발생한 경우 → 2차 호출
    if response.stop_reason == "tool_use":
        tool_results = [
            {
                "type": "tool_result",
                "tool_use_id": b.id,
                "content": f"검색어 '{getattr(b.input, 'query', str(b.input))}'에 대한 심평원 정보 검색 완료",
            }
            for b in blocks if b.type == "tool_use"
        ]
        response2 = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[
                *history,
                {"role": "assistant", "content": blocks},
                {"role": "user", "content": tool_results},
            ],
        )
        full_text = "".join(b.text for b in response2.content if hasattr(b, "text"))
    else:
        full_text = "".join(b.text for b in blocks if hasattr(b, "text"))

    return full_text or "검색 결과를 가져오지 못했습니다. hira.or.kr에서 직접 확인해주세요."


# ── 레이아웃 ──────────────────────────────────────────────
# 헤더
col_title, col_badge = st.columns([4, 1])
with col_title:
    st.markdown("## 🏥 급여기준 및 최신고시")
    st.caption("AI가 심평원(hira.or.kr)을 실시간으로 검색하여 최신 급여기준을 안내합니다.")
with col_badge:
    st.markdown('<div style="text-align:right;margin-top:16px"><span class="badge-live">🟢 실시간 검색</span></div>', unsafe_allow_html=True)

st.divider()

# 메인 2컬럼
left_col, right_col = st.columns([3, 1])

# ── 왼쪽: 검색 영역 ───────────────────────────────────────
with left_col:
    st.markdown("### 기준 검색")

    # API 키 확인
    api_key = get_api_key()
    if not api_key:
        with st.expander("🔑 API 키 설정 (로컬 테스트용)", expanded=True):
            key_input = st.text_input(
                "Anthropic API Key",
                type="password",
                placeholder="sk-ant-api03-...",
                help="console.anthropic.com에서 발급받으세요. 배포 환경에서는 Secrets에 설정하세요.",
            )
            if st.button("저장"):
                st.session_state.api_key = key_input
                st.rerun()

    # 빠른 검색 태그
    st.markdown("**빠른 검색**")
    tags = ["고혈압 약제 기준", "당뇨 검사 인정기준", "항생제 처방 기준",
            "주사제 심사사례", "MRI 급여기준", "초음파 인정기준"]
    tag_cols = st.columns(3)
    for i, tag in enumerate(tags):
        with tag_cols[i % 3]:
            if st.button(tag, key=f"tag_{i}", use_container_width=True):
                if api_key:
                    st.session_state.messages.append({"role": "user", "content": tag})
                    with st.spinner(f"🔍 '{tag}' 심평원 검색 중..."):
                        result = search_hira(tag, api_key)
                    st.session_state.messages.append({"role": "assistant", "content": result})
                    st.rerun()
                else:
                    st.warning("먼저 API 키를 설정해주세요.")

    st.markdown("---")

    # 대화 기록 표시
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-msg">🙋 {msg["content"]}</div><div style="clear:both"></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="result-header">🌐 심평원 실시간 검색 결과</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="result-box">{msg["content"]}</div>', unsafe_allow_html=True)

    # 검색 입력창
    st.markdown("---")
    query_col, btn_col = st.columns([5, 1])
    with query_col:
        query = st.text_input(
            "검색어 입력",
            placeholder="약제명, 상병명, 검사명 입력 (예: 메트포르민 인정기준)",
            label_visibility="collapsed",
        )
    with btn_col:
        search_clicked = st.button("검색", use_container_width=True)

    if search_clicked and query:
        if not api_key:
            st.error("API 키를 먼저 설정해주세요.")
        else:
            st.session_state.messages.append({"role": "user", "content": query})
            with st.spinner("🔍 심평원 실시간 검색 중..."):
                result = search_hira(query, api_key)
            st.session_state.messages.append({"role": "assistant", "content": result})
            st.rerun()

    if st.button("대화 초기화", type="secondary"):
        st.session_state.messages = []
        st.rerun()

# ── 오른쪽: 빠른 확인 + 링크 ─────────────────────────────
with right_col:
    st.markdown("### 빠른 확인")
    for label in st.session_state.checks:
        st.session_state.checks[label] = st.checkbox(
            label,
            value=st.session_state.checks[label],
            key=f"chk_{label}"
        )

    st.divider()
    st.markdown("**⚡ 실시간 검색 방식**")
    st.markdown("""
1. 검색어 입력  
2. AI가 심평원 사이트 검색  
3. 최신 고시 분석  
4. 인정기준 + 주의사항 정리  
5. 출처 URL 제공  
""")

    st.divider()
    st.markdown("**🔗 심평원 직접 접속**")
    st.markdown("[📋 보험인정기준](https://www.hira.or.kr/rc/insu/insuadtcrtr/InsuAdtCrtrList.do)")
    st.markdown("[🔍 심사기준 조회](https://m.hira.or.kr/mobile/rf/iac/eva/index.do)")
    st.markdown("[📢 공지사항·고시](https://www.hira.or.kr/bbsDummy.do?pgmid=HIRAA020002000100)")

    st.divider()
    st.warning("AI 검색 결과는 참고용입니다. 실제 청구 전 반드시 심평원 공식 고시를 확인하세요.")

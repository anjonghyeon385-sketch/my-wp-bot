import streamlit as st
import openai
import requests
import base64
from datetime import datetime

# --- [UI 설정 및 디자인 CSS] ---
st.set_page_config(page_title="AI WP Publisher", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경색 및 폰트 */
    .main { background-color: #f8f9fa; }
    
    /* 카드 스타일 디자인 */
    .content-card {
        background-color: white;
        padding: 30px;
        border-radius: 20px;
        border: 1px solid #e9ecef;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        margin-top: 20px;
    }
    
    /* 버튼 커스텀 */
    .stButton>button {
        border-radius: 12px;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        transition: all 0.2s ease-in-out;
    }
    
    .stButton>button:first-child { /* 생성 버튼 */
        background-color: #4F46E5;
        color: white;
        border: none;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 10px rgba(0,0,0,0.1);
    }
    
    /* 상태 표시바 */
    .status-bar {
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 20px;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [사이드바: 설정 정보] ---
with st.sidebar:
    st.header("⚙️ API 및 서버 설정")
    st.info("워드프레스와 OpenAI 정보를 입력하세요.")
    
    api_key = st.text_input("OpenAI API Key", type="password", help="OpenAI에서 발급받은 API 키를 입력하세요.")
    wp_url = st.text_input("WordPress URL", placeholder="https://your-site.com", help="워드프레스 주소를 입력하세요.")
    wp_user = st.text_input("WP Username", help="워드프레스 관리자 아이디를 입력하세요.")
    wp_app_pw = st.text_input("WP App Password", type="password", help="워드프레스 프로필에서 생성한 앱 비밀번호를 입력하세요.")
    
    st.divider()
    st.caption(f"© {datetime.now().year} AI WP Auto Bot v1.0")

# --- [핵심 기능 함수] ---
def generate_ai_content(topic, key):
    client = openai.OpenAI(api_key=key)
    try:
        with st.spinner('🤖 AI가 정보를 수집하고 글을 작성 중입니다...'):
            prompt = f"""
            주제: {topic}
            위 주제로 블로그 포스트를 작성해줘. 
            조건:
            1. SEO 최적화된 구조로 작성할 것 (h2, h3 태그 사용).
            2. 서론, 본론, 결론이 명확해야 함.
            3. HTML 형식으로 출력할 것.
            4. 한국어로 친절하게 작성할 것.
            """
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
    except Exception as e:
        st.error(f"AI 생성 오류: {e}")
        return None

def publish_to_wordpress(title, content):
    if not wp_url or not wp_user or not wp_app_pw:
        st.error("워드프레스 설정 정보가 부족합니다.")
        return False
    
    # REST API 경로 보정
    endpoint = f"{wp_url.rstrip('/')}/wp-json/wp/v2/posts"
    
    credentials = f"{wp_user}:{wp_app_pw}"
    token = base64.b64encode(credentials.encode()).decode()
    headers = {
        'Authorization': f'Basic {token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'title': title,
        'content': content,
        'status': 'publish'
    }
    
    try:
        res = requests.post(endpoint, headers=headers, json=payload)
        return res.status_code == 201
    except Exception as e:
        st.error(f"서버 통신 오류: {e}")
        return False

# --- [메인 UI] ---
st.title("🚀 Smart WP Publisher")
st.subheader("키워드 하나로 완성되는 워드프레스 자동 포스팅")

# 세션 상태 초기화 (글 저장용)
if 'generated_html' not in st.session_state:
    st.session_state.generated_html = ""
if 'current_topic' not in st.session_state:
    st.session_state.current_topic = ""

# 입력 구역
col1, col2 = st.columns([3, 1])
with col1:
    topic_input = st.text_input("포스팅 주제를 입력하세요", placeholder="예: 비트코인 투자 전망, 서울 맛집 베스트 5")
with col2:
    st.write(" ") # 간격 맞추기
    st.write(" ") 
    generate_btn = st.button("AI 글 생성")

# 실행 로직
if generate_btn:
    if not api_key:
        st.warning("먼저 왼쪽 사이드바에 OpenAI API Key를 입력해주세요.")
    elif not topic_input:
        st.warning("주제를 입력해주세요.")
    else:
        content = generate_ai_content(topic_input, api_key)
        if content:
            st.session_state.generated_html = content
            st.session_state.current_topic = topic_input

# 결과 표시 구역
if st.session_state.generated_html:
    st.markdown("---")
    
    # 미리보기 영역
    st.markdown(f"### 📝 '{st.session_state.current_topic}' 글 미리보기")
    with st.container():
        st.markdown(f'<div class="content-card">{st.session_state.generated_html}</div>', unsafe_allow_html=True)
    
    st.write(" ")
    
    # 워드프레스 전송 버튼
    if st.button("🌐 워드프레스에 실제 발행하기"):
        with st.spinner('워드프레스로 전송 중...'):
            success = publish_to_wordpress(st.session_state.current_topic, st.session_state.generated_html)
            if success:
                st.success("🎉 성공적으로 발행되었습니다! 블로그에서 확인해보세요.")
                st.balloons()
            else:
                st.error("발행에 실패했습니다. 사이드바의 설정을 다시 확인해주세요.")


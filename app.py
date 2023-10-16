import sentry_sdk
from sentry_sdk import capture_exception
import streamlit as st

from utils.discord_util import send_discord_message
from utils.firestore_util import save_result
from utils.google_util import upload_images
from utils.openai_util import request_chat_completion
from utils.streamlit_util import write_streaming_response

st.set_page_config(page_title="블로그매직", page_icon="✨")
sentry_sdk.set_tag("app", "blogmagic")

if 'sentry_initialized' not in st.session_state:
    sentry_sdk.init(
        dsn=st.secrets["SENTRY_KEY"],
        traces_sample_rate=0.01,
        profiles_sample_rate=0.01,
    )
    st.session_state.sentry_initialized = True


with st.sidebar:
    st.header("사용법")
    st.markdown("""
1. 포스팅 분야를 선택하고 주제를 적습니다.
2. 사용할 이미지를 순서대로 업로드합니다.
3. 각 이미지 별로 간단하게 설명을 적습니다.
4. 작성 버튼을 눌러서 포스팅을 생성합니다.
5. 그대로 드래그해서 복사해줍니다.
6. 네이버 블로그 글쓰기에 붙여넣습니다.
7. 서식과 텍스트를 수정하고 발행합니다.
8. 처음부터 다시하려면 새로고침 해주세요. 
    """)
    st.markdown("")
    st.header("개발자에게 전하고 싶은 말")
    with st.form("feedback", clear_on_submit=True):
        message = st.text_area(
            label="메세지",
            label_visibility="collapsed",
            placeholder="너무 잘 쓰고 있어요!",
        )
        submit = st.form_submit_button("✉️ 전송")
        if submit:
            send_discord_message(message_type="전하고 싶은 말", message=message)
    st.markdown("")
    st.markdown("Powered by gpt-3.5-turbo")
    st.markdown("""
**Youtube**: [퍼스트펭귄 코딩스쿨](https://www.youtube.com/channel/UCUFk9scQ-SqP993DRC4z_fA)  
**Blog**: https://blog.firstpenguine.school   
**Email**: hyeongjun.kim@firstpenguine.school
""")

st.title("블로그 매직✨")
st.markdown("이미지를 순서대로 첨부하고, 간단한 설명을 적어주면 AI가 블로그 포스팅을 완성해줍니다!")
st.markdown("""
<style>
p img {
    max-width: 400px;
    display: block;
}
header { visibility: hidden; }
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


def generate_prompt(subject, image_paths, descriptions):
    image_description = ""
    for image_path, description in zip(image_paths, descriptions):
        image_description += f"""
이미지 파일 경로: {image_path}
이미지 설명: {description}

"""

    prompt = f"""
포스팅 주제와 이미지 경로, 사진에 대한 간략한 설명이 주어집니다.
블로그 포스팅 제목과 본문을 재치있고 실감나게 작성해주세요.
클릭을 유도할 수 있는 창의적인 제목을 지어주세요.
마크다운 형식으로 작성해주세요.
이모지를 적절하게 사용하세요.
줄글로 풀어서 써주세요.
반드시 각 이미지별로 3문장에서 4문장 작성해주세요.
절대로 특정 블로거의 이름을 언급하면 안됩니다.
---
포스팅 주제: {subject}

{image_description}
---""".strip()
    return prompt


def input_description(images):
    for i, image in enumerate(images):
        cols = st.columns([0.2, 0.8])
        with cols[0]:
            st.image(image)
        with (cols[1]):
            st.text_area(
                label="이미지 설명",
                label_visibility="collapsed",
                key=f"description_{i}",
                placeholder="이미지에 대한 간단한 설명을 적어주세요 (선택)"
            )


col1, col2 = st.columns([0.3, 0.7])
with col1:
    area = st.selectbox(
        label="분야",
        options=["맛집리뷰", "IT리뷰", "영화 리뷰", "여행후기", "개발", "요리레시피", "일상", "육아", "기타"]
    )
with col2:
    subject = st.text_input(
        label="포스팅 주제",
        key="subject",
        placeholder="신사역 찐맛집 꿉당 리뷰"
    )
images = st.file_uploader(
    "이미지 파일 업로드(여러장 가능)",
    accept_multiple_files=True,
)

if not images:
    st.stop()
input_description(images)
write_button = st.button("✍️ 포스팅 작성하기")
if write_button:
    try:
        image_paths = upload_images(images)
    except Exception as e:
        st.error("이미지 업로드에 실패했습니다. 잠시 후에 다시 시도해주세요.")
        capture_exception(e)
        st.stop()
    descriptions = [st.session_state[f"description_{i}"] for i in range(len(images))]
    prompt = generate_prompt(subject, image_paths, descriptions)
    system_role = f"당신은 {area} 분야 전문 블로거입니다."
    messages = [{"role": "user", "content": prompt}]
    st.markdown("**생성된 텍스트는 그대로 드래그해서 복사한 다음, 블로그 글쓰기에 붙여넣으시면 됩니다.**")
    try:
        response = request_chat_completion(
            messages=messages,
            system_role=system_role
        )
    except Exception as e:
        st.error("chatGPT 요청에 실패했습니다. 잠시 후에 다시 시도해주세요.")
        capture_exception(e)
        st.stop()
    message = write_streaming_response(response)
    try:
        doc_id = save_result(image_paths, message)
        send_discord_message(
            message_type="블로그 자동완성",
            message=f"""
uploaded_images: {len(images)}
area: {area}
subject: {subject}
doc_id: {doc_id}
        """.strip())
    except Exception as e:
        capture_exception(e)

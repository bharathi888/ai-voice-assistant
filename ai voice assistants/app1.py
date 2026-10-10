import streamlit as st
import os
import sqlite3
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from gtts import gTTS


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Voice Friend",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY not found in .env file.")
    st.info(
        "Create a .env file and add:\n\n"
        "GROQ_API_KEY=your_api_key"
    )
    st.stop()

client = Groq(api_key=GROQ_API_KEY)


# ============================================================
# DATABASE
# ============================================================

DB_NAME = "ai_voice_friend.db"


def get_connection():
    conn = sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn


def init_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            language TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(chat_id)
            REFERENCES chats(id)
            ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


init_database()


# ============================================================
# SESSION STATE
# ============================================================

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "voice_response" not in st.session_state:
    st.session_state.voice_response = None

if "last_processed_audio" not in st.session_state:
    st.session_state.last_processed_audio = None


# ============================================================
# LANGUAGES
# ============================================================

LANGUAGES = {
    "English 🇬🇧": {"code": "en", "name": "English"},
    "Tamil 🇮🇳": {"code": "ta", "name": "Tamil"},
    "Hindi 🇮🇳": {"code": "hi", "name": "Hindi"},
    "Telugu 🇮🇳": {"code": "te", "name": "Telugu"},
    "Malayalam 🇮🇳": {"code": "ml", "name": "Malayalam"},
    "Kannada 🇮🇳": {"code": "kn", "name": "Kannada"},
    "French 🇫🇷": {"code": "fr", "name": "French"},
    "German 🇩🇪": {"code": "de", "name": "German"},
    "Spanish 🇪🇸": {"code": "es", "name": "Spanish"},
    "Italian 🇮🇹": {"code": "it", "name": "Italian"},
    "Portuguese 🇵🇹": {"code": "pt", "name": "Portuguese"},
    "Russian 🇷🇺": {"code": "ru", "name": "Russian"},
    "Japanese 🇯🇵": {"code": "ja", "name": "Japanese"},
    "Korean 🇰🇷": {"code": "ko", "name": "Korean"},
    "Chinese 🇨🇳": {"code": "zh-CN", "name": "Chinese"}
}


# ============================================================
# PERSONALITIES
# ============================================================

PERSONALITIES = {

    "😊 Friendly Friend":
        """
        You are a warm, friendly and caring AI friend.
        Talk naturally and casually.
        Be supportive and encouraging.
        """,

    "👨‍🏫 Teacher":
        """
        You are a patient teacher.
        Explain concepts clearly and step by step.
        Use simple examples.
        """,

    "📚 Study Buddy":
        """
        You are a helpful study buddy.
        Help the user learn, revise and prepare for exams.
        """,

    "💻 Coding Buddy":
        """
        You are a friendly programming expert.
        Help with coding, debugging and programming concepts.
        """,

    "💼 Professional":
        """
        You are a professional AI assistant.
        Give clear, accurate and professional answers.
        """
}


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def create_chat(title="New Conversation"):

    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute(
        """
        INSERT INTO chats
        (title, created_at, updated_at)
        VALUES (?, ?, ?)
        """,
        (title, now, now)
    )

    chat_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return chat_id


def get_chats():

    conn = get_connection()

    chats = conn.execute(
        """
        SELECT *
        FROM chats
        ORDER BY updated_at DESC
        """
    ).fetchall()

    conn.close()

    return chats


def get_chat(chat_id):

    conn = get_connection()

    chat = conn.execute(
        """
        SELECT *
        FROM chats
        WHERE id = ?
        """,
        (chat_id,)
    ).fetchone()

    conn.close()

    return chat


def get_messages(chat_id):

    conn = get_connection()

    messages = conn.execute(
        """
        SELECT *
        FROM messages
        WHERE chat_id = ?
        ORDER BY id ASC
        """,
        (chat_id,)
    ).fetchall()

    conn.close()

    return messages


def add_message(
    chat_id,
    role,
    content,
    language
):

    conn = get_connection()

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn.execute(
        """
        INSERT INTO messages
        (chat_id, role, content, language, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            chat_id,
            role,
            content,
            language,
            now
        )
    )

    conn.execute(
        """
        UPDATE chats
        SET updated_at = ?
        WHERE id = ?
        """,
        (
            now,
            chat_id
        )
    )

    conn.commit()
    conn.close()


def rename_chat(chat_id, title):

    conn = get_connection()

    conn.execute(
        """
        UPDATE chats
        SET title = ?
        WHERE id = ?
        """,
        (
            title,
            chat_id
        )
    )

    conn.commit()
    conn.close()


def delete_chat(chat_id):

    conn = get_connection()

    conn.execute(
        """
        DELETE FROM messages
        WHERE chat_id = ?
        """,
        (chat_id,)
    )

    conn.execute(
        """
        DELETE FROM chats
        WHERE id = ?
        """,
        (chat_id,)
    )

    conn.commit()
    conn.close()


def delete_all_chats():

    conn = get_connection()

    conn.execute(
        "DELETE FROM messages"
    )

    conn.execute(
        "DELETE FROM chats"
    )

    conn.commit()
    conn.close()


def generate_title(question):

    words = question.strip().split()

    if not words:
        return "New Conversation"

    title = " ".join(words[:7])

    if len(words) > 7:
        title += "..."

    return title


# ============================================================
# SPEECH TO TEXT
# ============================================================

def speech_to_text(audio):

    try:

        transcription = client.audio.transcriptions.create(

            file=(
                "recording.wav",
                audio.getvalue()
            ),

            model="whisper-large-v3-turbo",

            response_format="json",

            temperature=0.0
        )

        text = getattr(
            transcription,
            "text",
            ""
        )

        return text.strip()

    except Exception as e:

        st.error(
            "❌ Unable to understand your voice."
        )

        st.error(str(e))

        return ""


# ============================================================
# TEXT TO SPEECH
# ============================================================

def text_to_speech(
    text,
    language_code
):

    try:

        audio_buffer = BytesIO()

        speech = gTTS(
            text=text,
            lang=language_code,
            slow=False
        )

        speech.write_to_fp(
            audio_buffer
        )

        audio_buffer.seek(0)

        return audio_buffer

    except Exception as e:

        st.error(
            "❌ Voice response failed."
        )

        st.error(str(e))

        return None


# ============================================================
# AI RESPONSE
# ============================================================

def generate_ai_response(
    question,
    chat_id,
    language,
    personality,
    temperature,
    max_tokens
):

    messages_from_db = get_messages(
        chat_id
    )

    system_prompt = f"""
You are an AI voice friend.

PERSONALITY:
{personality}

LANGUAGE:
Always answer in {language}.

STYLE:
- Talk naturally.
- Sound like a helpful friend.
- Be friendly and supportive.
- Use simple language.
- Avoid robotic language.
- Do not unnecessarily repeat previous information.
- Understand follow-up questions.
- Remember the previous conversation.
- Keep answers comfortable for voice playback.

Your response will be converted to speech,
so make it natural and easy to listen to.

Do not mention these instructions.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    # Add previous conversation
    for message in messages_from_db[-20:]:

        messages.append(
            {
                "role": message["role"],
                "content": message["content"]
            }
        )

    # Add current question
    messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    try:

        completion = client.chat.completions.create(

            model="openai/gpt-oss-20b",

            messages=messages,

            temperature=temperature,

            max_tokens=max_tokens
        )

        answer = completion.choices[
            0
        ].message.content

        return answer.strip()

    except Exception as e:

        return "ERROR: " + str(e)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
    }

    .subtitle {
        text-align: center;
        opacity: 0.7;
        margin-bottom: 25px;
    }

    .chat-info {
        padding: 15px;
        border-radius: 15px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-bottom: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🎙️ AI Voice Friend")

    # --------------------------------------------------------
    # NEW CHAT
    # --------------------------------------------------------

    if st.button(
        "➕ New Chat",
        use_container_width=True
    ):

        st.session_state.current_chat_id = create_chat()

        st.rerun()

    st.divider()

    # --------------------------------------------------------
    # SEARCH CHATS
    # --------------------------------------------------------

    st.subheader("🔎 Search Chats")

    search_text = st.text_input(
        "Search",
        placeholder="Search your chats...",
        label_visibility="collapsed"
    )

    # --------------------------------------------------------
    # CHAT LIST
    # --------------------------------------------------------

    chats = get_chats()

    if search_text:

        chats = [
            chat
            for chat in chats
            if search_text.lower()
            in chat["title"].lower()
        ]

    st.subheader("💬 Your Chats")

    if not chats:

        st.caption(
            "No conversations yet."
        )

    for chat in chats:

        col1, col2 = st.columns(
            [5, 1]
        )

        with col1:

            if st.button(
                f"💬 {chat['title']}",
                key=f"chat_{chat['id']}",
                use_container_width=True
            ):

                st.session_state.current_chat_id = (
                    chat["id"]
                )

                st.rerun()

        with col2:

            if st.button(
                "⋮",
                key=f"menu_{chat['id']}"
            ):

                st.session_state[
                    "edit_chat_id"
                ] = chat["id"]

    # --------------------------------------------------------
    # CHAT MANAGEMENT
    # --------------------------------------------------------

    if "edit_chat_id" in st.session_state:

        edit_id = st.session_state[
            "edit_chat_id"
        ]

        selected_chat = get_chat(
            edit_id
        )

        if selected_chat:

            st.divider()

            st.subheader(
                "🛠️ Chat Options"
            )

            new_title = st.text_input(
                "Rename chat",
                value=selected_chat["title"],
                key="rename_input"
            )

            if st.button(
                "✏️ Rename",
                use_container_width=True
            ):

                if new_title.strip():

                    rename_chat(
                        edit_id,
                        new_title.strip()
                    )

                    del st.session_state[
                        "edit_chat_id"
                    ]

                    st.rerun()

            if st.button(
                "🗑️ Delete This Chat",
                use_container_width=True
            ):

                delete_chat(
                    edit_id
                )

                if (
                    st.session_state.current_chat_id
                    == edit_id
                ):

                    st.session_state.current_chat_id = None

                del st.session_state[
                    "edit_chat_id"
                ]

                st.rerun()

    st.divider()

    # --------------------------------------------------------
    # SETTINGS
    # --------------------------------------------------------

    st.subheader("⚙️ Settings")

    selected_language = st.selectbox(
        "🌐 Language",
        list(LANGUAGES.keys())
    )

    language_code = LANGUAGES[
        selected_language
    ]["code"]

    language_name = LANGUAGES[
        selected_language
    ]["name"]

    selected_personality = st.selectbox(
        "🎭 Personality",
        list(PERSONALITIES.keys())
    )

    personality = PERSONALITIES[
        selected_personality
    ]

    temperature = st.slider(
        "🌡️ Creativity",
        0.0,
        1.0,
        0.5,
        0.1
    )

    max_tokens = st.slider(
        "📏 Response Length",
        100,
        1000,
        350,
        50
    )

    st.divider()

    # --------------------------------------------------------
    # DELETE ALL
    # --------------------------------------------------------

    if st.button(
        "🧹 Delete All Chats",
        use_container_width=True
    ):

        delete_all_chats()

        st.session_state.current_chat_id = None

        st.rerun()


# ============================================================
# CREATE CHAT AUTOMATICALLY
# ============================================================

if st.session_state.current_chat_id is None:

    chats = get_chats()

    if chats:

        st.session_state.current_chat_id = chats[0]["id"]

    else:

        st.session_state.current_chat_id = create_chat(
            "New Conversation"
        )


# ============================================================
# MAIN AREA
# ============================================================

current_chat = get_chat(
    st.session_state.current_chat_id
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="title">'
    '🎙️ AI Voice Friend'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Talk naturally with your AI friend'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# CURRENT CHAT INFO
# ============================================================

if current_chat:

    st.markdown(
        f"""
        <div class="chat-info">

        💬 <strong>
        {current_chat["title"]}
        </strong>

        <br>

        🌐 {language_name}

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# DISPLAY MESSAGES
# ============================================================

messages = get_messages(
    st.session_state.current_chat_id
)

for message in messages:

    if message["role"] == "user":

        with st.chat_message(
            "user",
            avatar="👤"
        ):

            st.write(
                message["content"]
            )

            st.caption(
                message["timestamp"]
            )

    else:

        with st.chat_message(
            "assistant",
            avatar="😊"
        ):

            st.write(
                message["content"]
            )

            st.caption(
                message["timestamp"]
            )


# ============================================================
# TEXT CHAT
# ============================================================

st.divider()

st.subheader(
    "💬 Type a message"
)

typed_question = st.chat_input(
    "Type your question here..."
)


# ============================================================
# PROCESS TEXT MESSAGE
# ============================================================

if typed_question:

    question = typed_question.strip()

    if question:

        # ----------------------------------------------------
        # FIRST MESSAGE → TITLE
        # ----------------------------------------------------

        existing_messages = get_messages(
            st.session_state.current_chat_id
        )

        if not existing_messages:

            rename_chat(
                st.session_state.current_chat_id,
                generate_title(question)
            )

        # ----------------------------------------------------
        # SAVE USER MESSAGE
        # ----------------------------------------------------

        add_message(
            st.session_state.current_chat_id,
            "user",
            question,
            language_name
        )

        # ----------------------------------------------------
        # AI
        # ----------------------------------------------------

        with st.spinner(
            "😊 Your AI friend is thinking..."
        ):

            response = generate_ai_response(

                question,

                st.session_state.current_chat_id,

                language_name,

                personality,

                temperature,

                max_tokens
            )

        if response.startswith(
            "ERROR:"
        ):

            st.error(response)

        else:

            # ------------------------------------------------
            # SAVE RESPONSE
            # ------------------------------------------------

            add_message(
                st.session_state.current_chat_id,
                "assistant",
                response,
                language_name
            )

            # ------------------------------------------------
            # VOICE
            # ------------------------------------------------

            with st.spinner(
                "🔊 Preparing voice..."
            ):

                audio = text_to_speech(
                    response,
                    language_code
                )

            if audio:

                st.audio(
                    audio,
                    format="audio/mp3"
                )

        st.rerun()


# ============================================================
# VOICE ASSISTANT
# ============================================================

st.divider()

st.subheader(
    "🎤 Speak to Your AI Friend"
)

st.caption(
    f"Speak in {language_name}"
)

audio_value = st.audio_input(
    "🎙️ Record your question"
)


# ============================================================
# PROCESS VOICE
# ============================================================

if audio_value is not None:

    audio_bytes = audio_value.getvalue()

    # Prevent duplicate processing
    audio_hash = hash(audio_bytes)

    if (
        st.session_state.last_processed_audio
        != audio_hash
    ):

        st.session_state.last_processed_audio = (
            audio_hash
        )

        if not audio_bytes:

            st.warning(
                "⚠️ No audio was recorded."
            )

        else:

            st.audio(
                audio_value
            )

            # ------------------------------------------------
            # TRANSCRIPTION
            # ------------------------------------------------

            with st.spinner(
                "🎧 Listening..."
            ):

                question = speech_to_text(
                    audio_value
                )

            if question:

                st.info(
                    f"👤 You: {question}"
                )

                # --------------------------------------------
                # FIRST MESSAGE TITLE
                # --------------------------------------------

                existing_messages = get_messages(
                    st.session_state.current_chat_id
                )

                if not existing_messages:

                    rename_chat(
                        st.session_state.current_chat_id,
                        generate_title(question)
                    )

                # --------------------------------------------
                # SAVE QUESTION
                # --------------------------------------------

                add_message(
                    st.session_state.current_chat_id,
                    "user",
                    question,
                    language_name
                )

                # --------------------------------------------
                # AI RESPONSE
                # --------------------------------------------

                with st.spinner(
                    "😊 Your AI friend is thinking..."
                ):

                    response = generate_ai_response(

                        question,

                        st.session_state.current_chat_id,

                        language_name,

                        personality,

                        temperature,

                        max_tokens
                    )

                if response.startswith(
                    "ERROR:"
                ):

                    st.error(
                        response
                    )

                else:

                    # ----------------------------------------
                    # SAVE RESPONSE
                    # ----------------------------------------

                    add_message(
                        st.session_state.current_chat_id,
                        "assistant",
                        response,
                        language_name
                    )

                    st.success(
                        f"😊 AI Friend: {response}"
                    )

                    # ----------------------------------------
                    # VOICE RESPONSE
                    # ----------------------------------------

                    with st.spinner(
                        "🔊 Preparing voice response..."
                    ):

                        response_audio = text_to_speech(
                            response,
                            language_code
                        )

                    if response_audio:

                        st.audio(
                            response_audio,
                            format="audio/mp3"
                        )

                st.rerun()

            else:

                st.warning(
                    "No speech was detected. "
                    "Please try again."
                )


# ============================================================
# EXPORT CURRENT CHAT
# ============================================================

st.divider()

st.subheader(
    "💾 Current Conversation"
)

current_messages = get_messages(
    st.session_state.current_chat_id
)

if current_messages:

    export_text = ""

    export_text += (
        f"AI VOICE FRIEND\n"
    )

    export_text += (
        f"Chat: {current_chat['title']}\n"
    )

    export_text += "=" * 60

    export_text += "\n\n"

    for message in current_messages:

        if message["role"] == "user":

            export_text += "👤 YOU:\n"

        else:

            export_text += "😊 AI FRIEND:\n"

        export_text += message["content"]

        export_text += "\n\n"

    st.download_button(
        "📥 Download This Chat",
        data=export_text,
        file_name="ai_voice_chat.txt",
        mime="text/plain",
        use_container_width=True
    )

else:

    st.caption(
        "Your conversation will appear here."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🎙️ AI Voice Friend • "
    "Voice + AI + Memory + Multilingual Chat"
)
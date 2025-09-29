
import os
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import re

# 環境変数の読み込み（ローカル開発用のみ）
def load_env_if_available():
    """dotenvが利用可能な場合のみ.envファイルを読み込む"""
    try:
        from dotenv import load_dotenv
        load_dotenv()  # 現在のディレクトリ
        load_dotenv('.env')  # 明示的に.envファイル指定
        load_dotenv('streamlit-llm-app/.env')  # サブディレクトリも確認
        return True
    except (ImportError, Exception):
        # dotenvが利用できない場合（Streamlit Cloudなど）はスキップ
        return False

# 環境変数読み込み実行
env_loaded = load_env_if_available()

# OpenAI APIキーの確認
def get_openai_api_key():
    """複数のソースからOpenAI APIキーを取得"""
    # 1. 環境変数から取得
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key, "環境変数"
    
    # 2. Streamlit Secretsから取得
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        if api_key:
            return api_key, "Streamlit Secrets"
    except (KeyError, FileNotFoundError):
        pass
    
    return None, None

openai_api_key, source = get_openai_api_key()

if not openai_api_key:
    st.error("⚠️ OpenAI APIキーが設定されていません。")
    st.error("**Streamlit Cloudをご利用の場合:**")
    st.code("1. アプリの管理画面で 'Settings' > 'Secrets' を開く")
    st.code("2. 以下を追加: OPENAI_API_KEY = \"your_actual_api_key\"")
    
    st.error("**ローカル開発の場合:**")
    st.code("1. .envファイル: OPENAI_API_KEY=your_key")
    st.code("2. 環境変数: set OPENAI_API_KEY=your_key")
    st.stop()


# LLMの初期化
try:
    llm = ChatOpenAI(
        model_name="gpt-4o-mini", 
        temperature=0,
        openai_api_key=openai_api_key
    )
except Exception as e:
    st.error(f"❌ LLMの初期化に失敗しました: {str(e)}")
    st.stop()

# カテゴリー設定
CATEGORIES = {
    "健康": {
        "description": "健康に関するお悩みですね。",
        "system_prompt": "あなたは健康に関する専門家です。お悩みに対して親身に答えてください。",
        "keywords": ["病気", "体調", "症状", "健康", "医療", "薬", "治療", "痛み", "疲れ", "睡眠", "運動", "食事"]
    },
    "お金": {
        "description": "お金に関するお悩みですね。",
        "system_prompt": "あなたはお金に関する専門家です。お悩みに対して親身に答えてください。",
        "keywords": ["お金", "貯金", "投資", "家計", "節約", "借金", "ローン", "給料", "収入", "支出", "税金", "年金"]
    },
    "人間関係": {
        "description": "人間関係に関するお悩みですね。",
        "system_prompt": "あなたは人間関係に関する専門家です。お悩みに対して親身に答えてください。",
        "keywords": ["友達", "恋人", "家族", "職場", "上司", "部下", "同僚", "コミュニケーション", "喧嘩", "恋愛", "結婚", "離婚"]
    },
    "仕事": {
        "description": "仕事に関するお悩みですね。",
        "system_prompt": "あなたは仕事に関する専門家です。お悩みに対して親身に答えてください。",
        "keywords": ["仕事", "転職", "就職", "キャリア", "スキル", "残業", "ストレス", "会社", "職場", "昇進", "評価", "プロジェクト"]
    }
}

def validate_input(text):
    """入力内容の妥当性をチェック"""
    if not text or text.strip() == "":
        return False, "お悩みを入力してください。"
    
    if len(text.strip()) < 5:
        return False, "お悩みをもう少し詳しく入力してください（5文字以上）。"
    
    if len(text) > 500:
        return False, "入力文字数が多すぎます（500文字以内でお願いします）。"
    
    # 不適切な内容のチェック（簡易版）
    inappropriate_words = ["死にたい", "自殺", "殺", "爆弾"]
    if any(word in text for word in inappropriate_words):
        return False, "申し訳ありませんが、この内容についてはお答えできません。専門機関にご相談をお勧めします。"
    
    return True, ""

def check_category_relevance(text, category):
    """入力内容とカテゴリーの関連性をチェック"""
    keywords = CATEGORIES[category]["keywords"]
    text_lower = text.lower()
    
    # キーワードマッチング
    matched_keywords = [keyword for keyword in keywords if keyword in text_lower]
    
    if not matched_keywords:
        return False, f"⚠️ 入力内容が「{category}」カテゴリーと関連していない可能性があります。適切なカテゴリーを選択し直すか、{category}に関連する内容で入力し直してください。"
    
    return True, ""

def get_ai_response(category, user_input):
    """AIからの回答を取得"""
    try:
        category_info = CATEGORIES[category]
        messages = [
            SystemMessage(content=category_info["system_prompt"]),
            HumanMessage(content=user_input),
        ]
        result = llm(messages)
        return result.content
    except Exception as e:
        return f"申し訳ありません。回答の生成中にエラーが発生しました。しばらく時間をおいてから再度お試しください。\nエラー詳細: {str(e)}"

# Streamlitアプリの設定
st.title("🤖 お悩み相談AI")
st.markdown("### あなたのお悩みを選択したカテゴリーに応じてAIがアドバイスします")

selected_worries = st.radio(
    "相談したいお悩みを選択してください。",
    list(CATEGORIES.keys())
)

st.divider()

# 選択されたカテゴリーの処理
if selected_worries in CATEGORIES:
    category_info = CATEGORIES[selected_worries]
    st.write(f"📝 {category_info['description']}")
    
    input_text = st.text_area(
        "あなたのお悩みを詳しく入力してください。",
        placeholder=f"{selected_worries}に関するお悩みを具体的に書いてください...",
        max_chars=500
    )
    
    if input_text:
        # 入力内容の妥当性チェック
        is_valid, validation_message = validate_input(input_text)
        
        if not is_valid:
            st.error(validation_message)
        else:
            # カテゴリーとの関連性チェック
            is_relevant, relevance_message = check_category_relevance(input_text, selected_worries)
            
            if not is_relevant:
                st.warning(relevance_message)
                
                # それでも続行するかユーザーに確認
                if st.button("それでもこのカテゴリーで相談する"):
                    with st.spinner("回答を生成中..."):
                        response = get_ai_response(selected_worries, input_text)
                        st.success("✅ 回答")
                        st.write(response)
            else:
                # 正常な処理
                with st.spinner("回答を生成中..."):
                    response = get_ai_response(selected_worries, input_text)
                    st.success("✅ 回答")
                    st.write(response)

else:
    # 想定外のカテゴリーが選択された場合（念のため）
    st.error("⚠️ 申し訳ありません。選択されたカテゴリーは現在サポートされていません。")

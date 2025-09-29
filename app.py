
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import re

# LLMの初期化
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

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

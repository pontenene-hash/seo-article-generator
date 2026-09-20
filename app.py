import os
from typing import Optional

import streamlit as st
from google import genai
from google.genai import types


st.set_page_config(page_title="SEO記事自動生成", page_icon="✍️", layout="centered")


SYSTEM_PROMPT = """あなたは月間100万PV規模のメディアを支援する、日本語SEOコンサルタント兼Webライターです。
読者の課題解決を最優先し、誇張、根拠のない断定、キーワードの不自然な詰め込みを避けてください。
医療・健康・法律・金融などの重要分野では診断や保証をせず、必要に応じて専門家への相談を促してください。
出力は指定された内容だけを日本語Markdownで返してください。"""


def secret_value(name: str) -> Optional[str]:
    """Streamlit Secrets → environment variable の順で設定を読む。"""
    try:
        value = st.secrets.get(name)
        if value:
            return str(value)
    except (FileNotFoundError, KeyError):
        pass
    return os.getenv(name)


def call_llm(client: genai.Client, model: str, prompt: str, max_output_tokens: int) -> str:
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=max_output_tokens,
            temperature=0.7,
        ),
    )
    result = (response.text or "").strip()
    if not result:
        raise RuntimeError("生成結果が空でした。もう一度お試しください。")
    return result


def analyze_search_intent(client: genai.Client, model: str, keyword: str) -> str:
    return call_llm(
        client,
        model,
        f"""【ステップ1：検索意図の分析】
対策キーワード：{keyword}

このキーワードで検索する想定読者を具体化し、次の項目を分析してください。
- 想定読者像
- 表面的な悩み
- 本人も言語化しにくい深い悩み
- 検索直後に知りたいこと
- 最終的に達成したい状態
- 検索意図（Know / Do / Go / Buy）
- 記事で解消すべき不安・疑問

競合記事を実際に閲覧したとは表現しないでください。見出しは「想定読者の悩み」とし、簡潔かつ具体的にまとめてください。""",
        3000,
    )


def create_outline(client: genai.Client, model: str, keyword: str, intent: str) -> str:
    return call_llm(
        client,
        model,
        f"""【ステップ2：記事構成の作成】
対策キーワード：{keyword}

以下の検索意図分析を踏まえてください。
---
{intent}
---

検索者の疑問が自然な順序で解決する、論理的で網羅的な構成を作成してください。
条件：
- SEOタイトル案を1つ作る
- 導入文で扱う内容を示す
- H2は5〜8個を目安にする
- 必要なH2の下にH3を2〜4個置く
- 見出しだけで記事全体の流れが分かるようにする
- 同じ内容の重複を避ける
- 最後は「まとめ」とし、自然な次の行動につなげる
- Markdownの # / ## / ### を使う

見出しは「記事の構成案」としてください。""",
        4500,
    )


def write_article(client: genai.Client, model: str, keyword: str, intent: str, outline: str) -> str:
    return call_llm(
        client,
        model,
        f"""【ステップ3：本文執筆】
対策キーワード：{keyword}

検索意図分析：
---
{intent}
---

確定した構成案：
---
{outline}
---

上記の構成を変更せず、日本語の完成原稿を執筆してください。
執筆条件：
- SEOタイトル、導入文、すべてのH2・H3、まとめを含める
- 各見出しではPREP法（結論→理由→具体例→結論）を基本にする
- PREPのラベルは本文に表示せず、自然な文章にする
- 初心者にも分かる、やさしく信頼感のある文体にする
- 対策キーワードと関連語を文脈に沿って自然に使う
- 冗長な繰り返し、過度な煽り、事実未確認の数値や出典を避ける
- 目安は5,000〜8,000字。内容の充実を優先する
- Markdown形式で、そのままブログへ編集・転載しやすくする

見出しは「完成した本文」としてください。""",
        16000,
    )


def show_result(title: str, content: str) -> None:
    st.subheader(title)
    with st.container(border=True):
        st.markdown(content)


st.title("SEO記事自動生成")
st.caption("対策キーワードを入力するだけで、検索意図・構成案・本文をまとめて作成します。")

with st.sidebar:
    st.header("Gemini API設定")
    saved_key = secret_value("GEMINI_API_KEY")
    api_key_input = st.text_input(
        "Gemini APIキー",
        type="password",
        placeholder="Google AI Studioで取得したキー",
        help="Secretsに保存済みの場合は入力不要です。入力値はファイルに保存されません。",
    )
    model = st.text_input(
        "使用モデル",
        value=secret_value("GEMINI_MODEL") or "gemini-3.5-flash",
        help="利用できるGeminiモデル名を入力してください。",
    )
    if saved_key:
        st.success("保存済みのAPIキーを使用できます。")
    st.success("無料枠の対象モデルを初期設定しています。")
    st.warning("無料枠では、入力内容がGoogle製品の改善に利用される場合があります。氏名・住所・症例などの個人情報は入力しないでください。")

keyword = st.text_input(
    "対策キーワード",
    placeholder="例：せんげん台 整体",
    label_visibility="collapsed",
)
generate = st.button("記事を生成する", type="primary", use_container_width=True)

if generate:
    keyword = keyword.strip()
    api_key = api_key_input.strip() or saved_key
    model = model.strip()

    if not keyword:
        st.warning("対策キーワードを入力してください。")
        st.stop()
    if not api_key:
        st.error("左側の「Gemini API設定」からAPIキーを入力してください。")
        st.stop()
    if not model:
        st.error("使用モデルを入力してください。")
        st.stop()

    client = genai.Client(api_key=api_key)
    progress = st.progress(0, text="ステップ1/3：想定読者の悩みを分析しています…")

    try:
        intent = analyze_search_intent(client, model, keyword)
        progress.progress(34, text="ステップ2/3：記事の構成案を作成しています…")
        outline = create_outline(client, model, keyword, intent)
        progress.progress(67, text="ステップ3/3：PREP法で本文を執筆しています…")
        article = write_article(client, model, keyword, intent, outline)
        progress.progress(100, text="記事の生成が完了しました。")

        st.session_state["seo_result"] = {
            "keyword": keyword,
            "intent": intent,
            "outline": outline,
            "article": article,
        }
    except Exception as exc:
        error_text = str(exc)
        if "API_KEY_INVALID" in error_text or "401" in error_text or "403" in error_text:
            st.error("Gemini APIキーを確認してください。認証に失敗しました。")
        elif "RESOURCE_EXHAUSTED" in error_text or "429" in error_text:
            st.error("Gemini無料枠の利用上限に達しました。時間をおいて、もう一度お試しください。料金は発生しません。")
        elif "not found" in error_text.lower() or "404" in error_text:
            st.error("指定したモデルを利用できません。左側のモデル名を確認してください。")
        else:
            st.error(f"生成中にエラーが発生しました：{error_text}")


if "seo_result" in st.session_state:
    result = st.session_state["seo_result"]
    st.divider()
    st.caption(f"対策キーワード：{result['keyword']}")
    show_result("1. 想定読者の悩み", result["intent"])
    show_result("2. 記事の構成案", result["outline"])
    show_result("3. 完成した本文", result["article"])

    download_text = (
        f"# 対策キーワード\n\n{result['keyword']}\n\n"
        f"# 想定読者の悩み\n\n{result['intent']}\n\n"
        f"# 記事の構成案\n\n{result['outline']}\n\n"
        f"# 完成した本文\n\n{result['article']}\n"
    )
    st.download_button(
        "生成結果をMarkdownでダウンロード",
        data=download_text.encode("utf-8-sig"),
        file_name="seo_article.md",
        mime="text/markdown",
        use_container_width=True,
    )

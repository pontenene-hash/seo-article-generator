# SEO記事自動生成アプリ

対策キーワードを1つ入力すると、Gemini APIの無料枠を使って次の3工程を順番に実行するStreamlitアプリです。

1. 想定読者の深い悩みと検索意図を分析
2. H2・H3の見出し構成を作成
3. 構成に沿ってPREP法で記事本文を執筆

## 画面

メイン画面には「対策キーワード」「あなたの体験談や独自ノウハウのメモ（任意）」「記事を生成する」ボタンがあります。APIキーとモデルの設定は左側のサイドバーに分離しています。生成後は「想定読者の悩み」「記事の構成案」「完成した本文」「WordPress貼り付け用HTML」を分けて表示し、Markdown形式とHTML形式で保存できます。

## パソコンで起動する方法

Python 3.10以上を推奨します。フォルダ内でターミナルを開き、次を順番に実行してください。

```bash
python -m venv .venv
```

Windowsの場合：

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Macの場合：

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

ブラウザが自動で開きます。開かない場合は、ターミナルに表示される `http://localhost:8501` をブラウザで開いてください。

## APIキーの設定

### 手軽な方法

1. [Google AI Studio](https://aistudio.google.com/apikey)を開き、Googleアカウントでログインします。
2. 「APIキーを作成」を選び、表示されたキーをコピーします。
3. アプリ左側の「Gemini API設定」に貼り付けます。

入力値はアプリのファイルには保存されません。無料で使う場合は、Google AI Studioで有料請求を設定する必要はありません。

### 毎回の入力を省く方法

`.streamlit/secrets.toml.example` を `.streamlit/secrets.toml` という名前でコピーし、APIキーを書き換えます。

```toml
GEMINI_API_KEY = "実際のGemini APIキー"
GEMINI_MODEL = "gemini-3.5-flash-lite"
```

`secrets.toml` はGitHubへアップロードしないでください。このプロジェクトの `.gitignore` では除外設定済みです。

## Streamlit Community Cloudへ公開する方法

1. このフォルダ内のファイルをGitHubリポジトリへアップロードします。
2. Streamlit Community Cloudでリポジトリ、ブランチ、`app.py` を指定します。
3. アプリの **Settings → Secrets** に次を登録します。

```toml
GEMINI_API_KEY = "実際のGemini APIキー"
GEMINI_MODEL = "gemini-3.5-flash-lite"
```

4. 保存後にアプリを再起動します。

## 注意事項

- 初期設定の `gemini-3.5-flash-lite` は、Googleが無料枠を提供している間は無料枠内で利用できます。
- 混雑時は自動再試行し、解消しない場合は別の無料モデルへ切り替えます。
- Step 2の構成をH2見出し単位に分割し、H2の数だけ繰り返して詳しく執筆します。H3は親H2と同じ回で執筆します。
- 各H2セクションは1,200〜2,000字を目安に生成します。
- 途中で止まっても完成済みの見出しを保持し、「途中から再開する」で次の見出しから生成できます。
- 入力内で事実確認できない数値、統計、研究結果、引用、制度、固有名詞、効果保証、架空の事例は出力しません。
- 任意の体験談・独自ノウハウのメモを、記事の冒頭と結論へ自然に反映します。メモにない内容は創作せず、個人の体験を一般化しません。
- 完成本文からWordPress用HTMLを自動作成します。見出しは見出しタグ、重要語は `<strong>`、手順は `<ul>` と `<li>` へ変換します。
- HTML版は追加のAPI呼び出しを行わないため、Markdown版と内容が一致し、無料枠も追加消費しません。
- 各工程でAPIを呼ぶため、無料枠の利用回数・トークン上限を消費します。
- 無料枠の上限に達した場合は生成が停止します。時間をおいて再実行してください。
- 有料請求を設定しない限り、このアプリから自動的に有料枠へ切り替わることはありません。
- 無料枠では入力・出力がGoogle製品の改善に利用される場合があります。患者様・お客様の氏名、住所、症例などの個人情報は入力しないでください。
- AI生成文には誤りが含まれる可能性があります。公開前に事実確認、表現調整、独自情報の追加を行ってください。
- この版はGoogle検索結果や競合ページを直接調査しません。入力キーワードと生成AIの推論をもとに検索意図を分析します。

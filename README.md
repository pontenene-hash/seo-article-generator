# SEO記事自動生成アプリ

対策キーワードを1つ入力すると、Gemini APIの無料枠を使って次の3工程を順番に実行するStreamlitアプリです。

1. 想定読者の深い悩みと検索意図を分析
2. H2・H3の見出し構成を作成
3. 構成に沿ってPREP法で記事本文を執筆

## 画面

メイン画面は「対策キーワード」と「記事を生成する」ボタンだけです。APIキーとモデルの設定は左側のサイドバーに分離しています。生成後は「想定読者の悩み」「記事の構成案」「完成した本文」を分けて表示し、Markdown形式でも保存できます。

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
- 長い本文を前半・後半に分けて生成し、途中で止まっても完成済み部分を保持します。
- 途中停止後は「途中から再開する」で、未完成部分だけを生成できます。
- 各工程でAPIを呼ぶため、無料枠の利用回数・トークン上限を消費します。
- 無料枠の上限に達した場合は生成が停止します。時間をおいて再実行してください。
- 有料請求を設定しない限り、このアプリから自動的に有料枠へ切り替わることはありません。
- 無料枠では入力・出力がGoogle製品の改善に利用される場合があります。患者様・お客様の氏名、住所、症例などの個人情報は入力しないでください。
- AI生成文には誤りが含まれる可能性があります。公開前に事実確認、表現調整、独自情報の追加を行ってください。
- この版はGoogle検索結果や競合ページを直接調査しません。入力キーワードと生成AIの推論をもとに検索意図を分析します。

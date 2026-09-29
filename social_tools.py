import json
import re


MEDIA_FILENAMES = {
    "x_image": "X_投稿画像.png",
    "facebook_eyecatch": "Facebook_アイキャッチ.png",
    "gbp_image": "GBP_投稿画像.png",
    "threads_image": "Threads_投稿画像.png",
    "reel_cover": "Instagram_リール表紙.png",
    "reel_video": "Instagram_リール動画.mp4",
    "youtube_thumbnail": "YouTube_サムネイル.png",
    "youtube_video": "YouTube_動画.mp4",
    "tiktok_cover": "TikTok_表紙.png",
    "tiktok_video": "TikTok_動画.mp4",
}

IMAGE_QUALITY = (
    "あなたは読者心理と購買行動を熟知したプロのマーケティングコンサルタントであり、"
    "広告・出版分野で経験豊富なプロのイラストレーターです。マーケティング視点で情報の優先順位と視線誘導を設計し、"
    "細部まで丁寧で求心力のある高品質な商用イラストを制作する。"
    "読者の感情が伝わる自然な表情と仕草、正確な人体、丁寧な手指、内容に合う背景と小物、柔らかな自然光、"
    "奥行きと質感、清潔感・信頼感・親しみやすさを備えた現代的な日本の雑誌広告風。"
    "安価な素材集風、幼すぎる絵、棒人間、平面的で単調な構図、不自然な手指、過剰な医療表現、"
    "実在ロゴ、著名キャラクター、特定作家の画風、透かし、意味不明な文字を使用しない。"
)

BRIGHT_VISUAL_RULES = (
    "全体は明るく魅力的なハイキー表現にし、白を基調に、コーラル、明るい黄色、空色、ミントなどを内容に合わせて調和させる。"
    "彩度は生き生きと見える範囲に保ち、白飛びや派手すぎる原色は避ける。柔らかな日差し、透明感のある空気、"
    "清潔な背景、自然な笑顔または前向きな表情、親しみやすく自然な動作で、見た人が内容を知りたくなる第一印象を作る。"
    "主役がひと目で分かる焦点、前景・中景・背景の奥行き、記事内容を補う小物を丁寧に描き、上質な雑誌広告のように仕上げる。"
    "暗い画面、灰色や茶色に偏った配色、濁った低彩度、重苦しい影、無表情、恐怖をあおる表現、"
    "汎用素材のような笑顔の人物だけの構図、内容と無関係な装飾は禁止する。"
)

CONTENT_VISUAL_RULES = (
    "制作前に見出し・説明・場面指定を読み、①記事で伝える要点、②その要点に関係する読者の状況、"
    "③理解または実践後の望ましい変化を整理する。イラストは、その場面の要点が文字を読まなくても伝わるよう、"
    "人物、表情、視線、手の動き、姿勢、場所、背景、小物を具体的に組み合わせる。"
    "記事にない効果、数値、設備、資格、人物、商品、店舗情報は描き足さない。"
)

TEXT_LAYOUT_RULES = (
    "文字を描画する前に、全文を日本語として読み、文節・語句・固有名詞・熟語の境界を確認して改行位置を確定する。"
    "確定した各行を分割禁止の1つのテキストオブジェクトとして配置し、制作ツールによる自動折り返しを無効にする。"
    "単語、固有名詞、商品名、施設名、熟語、数字と単位の途中では絶対に改行しない。"
    "助詞、句読点、長音、閉じ括弧を行頭に置かず、1文字だけの行や極端に短い行を作らない。"
    "改行後は各行の見た目の横幅を揃え、中央揃えを基本に、行間・字間・左右余白を再調整する。"
    "上段だけ長い、下段だけ短い、片側へ寄る構成を避け、テキストブロック全体の重心を中央に整える。"
)

PROFESSIONAL_REVIEW = (
    "納品前に、プロのイラストレーター兼アートディレクターとして100％表示とスマートフォン縮小表示の両方で最終検品する。"
    "検品項目は、誤字、文字化け、単語途中の改行、行頭禁則、各行の長さ、文字の中央揃え、行間、余白、視覚的重心、"
    "文字と人物の重なり、領域越境、人物の顔・手指・身体、小物、背景、色、コントラスト、媒体サイズである。"
    "1項目でも不合格なら内部でレイアウトまたはイラストを修正して再検品し、すべて合格した完成版だけを出力する。"
    "ラフ、途中経過、未検品版、複数候補は出力しない。"
)


def _strip_code_fence(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _load_json_response(raw: str) -> dict:
    cleaned = _strip_code_fence(raw)
    candidates = [cleaned]
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start >= 0 and end > start:
        candidates.append(cleaned[start : end + 1])
    for candidate in candidates:
        try:
            data = json.loads(re.sub(r",\s*([}\]])", r"\1", candidate))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            continue
    raise json.JSONDecodeError("SNS構成のJSONを解析できません。", cleaned, 0)


def _plain_text(value: str, limit: int = 100) -> str:
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", str(value or ""))
    value = re.sub(r"[*_`>#]", "", value)
    return re.sub(r"\s+", " ", value).strip()[:limit]


def _safe_filename_part(value: str, limit: int = 24) -> str:
    value = re.sub(r'[\\/:*?"<>|]', "", _plain_text(value, limit))
    return re.sub(r"\s+", "_", value).strip("._") or "記事セクション"


def _first_scene_visual(item: dict) -> str:
    scenes = item.get("scenes", []) if isinstance(item, dict) else []
    first = scenes[0] if scenes and isinstance(scenes[0], dict) else {}
    return _plain_text(first.get("visual", ""), 180)


def _article_sections(article: str) -> list[dict]:
    sections, current, body = [], None, []
    for raw in article.splitlines():
        match = re.match(r"^(#{2,3})\s+(.+)$", raw.strip())
        if match:
            if current:
                current["summary"] = _plain_text(" ".join(body), 140)
                sections.append(current)
            current = {
                "level": "H2" if len(match.group(1)) == 2 else "H3",
                "heading": _plain_text(match.group(2), 36),
            }
            body = []
        elif current and raw.strip():
            body.append(raw.strip())
    if current:
        current["summary"] = _plain_text(" ".join(body), 140)
        sections.append(current)
    return sections[:30]


def _article_image_sections(article: str, maximum: int = 6) -> list[dict]:
    """記事画像は重要なH2だけに絞り、長い記事でも作り過ぎない。"""
    sections = _article_sections(article)
    h2_sections = [section for section in sections if section.get("level") == "H2"]
    candidates = h2_sections or sections
    if len(candidates) <= maximum:
        return candidates

    # 冒頭・中盤・終盤から均等に選び、記事全体を過不足なくカバーする。
    positions = [round(index * (len(candidates) - 1) / (maximum - 1)) for index in range(maximum)]
    return [candidates[position] for position in positions]


def _normalize_plan(data: dict, article: str) -> dict:
    if not isinstance(data, dict):
        raise ValueError("SNS構成が正しい形式ではありません。")
    carousel = data.setdefault("carousel", {})
    if not isinstance(carousel, dict):
        carousel = {}
        data["carousel"] = carousel
    slides = carousel.get("slides", [])
    if not isinstance(slides, list):
        slides = []
    sections = _article_sections(article)
    while len(slides) < 9:
        source = sections[min(len(slides), len(sections) - 1)] if sections else {}
        slides.append({
            "title": source.get("heading", "まとめ" if len(slides) == 8 else f"ポイント{len(slides) + 1}"),
            "body": source.get("summary", "記事の要点を分かりやすく確認しましょう。")[:80],
            "visual": (
                f"『{source.get('heading', '記事のポイント')}』の内容を理解または実践している読者。"
                f"要点は『{source.get('summary', '記事の内容を確認する')}』。内容に合う場所、表情、動作、小物を描く"
            ),
        })
    carousel["slides"] = slides[:9]
    return data


def _image_prompt_item(
    title: str,
    body: str,
    size: str,
    layout: str,
    font_spec: str,
    filename: str,
    scene: str = "",
) -> dict:
    title = _plain_text(title, 22) or "記事のポイント"
    body = _plain_text(body, 55)
    visual_direction = _plain_text(scene or f"{title}。{body}", 180)
    prompt = (
        "キャンバスをイラスト表示エリアとテキスト専用エリアの2領域へ完全分離する。"
        f"{IMAGE_QUALITY}{BRIGHT_VISUAL_RULES}{CONTENT_VISUAL_RULES}"
        f"出力サイズは{size}。この画像が担当する記事の要点と具体的な場面は『{visual_direction}』。"
        "抽象的な飾りや汎用的な人物に置き換えず、この要点に固有の状況を中心に描く。"
        f"レイアウトは{layout}。テキスト専用エリアへ見出し『{title}』"
        + (f"、補足『{body}』" if body else "")
        + "を一字一句正確に入れる。イラスト領域には人物・背景・小物だけを描き、文字・数字・帯・吹き出しを置かない。"
        "テキスト領域には人物や重要なイラストを置かず、両領域を1ピクセルも越境させない。人物の顔、手、重要な小物を文字で隠さない。"
        f"フォントは{font_spec}。{TEXT_LAYOUT_RULES}"
        "補足（サブテキスト）のフォントサイズは、見出し（メインテキスト）の約80％にする。"
        "文字が収まらない場合はフォントを小さくせず文章を短くする。高コントラストと十分な安全余白を確保する。"
        f"{PROFESSIONAL_REVIEW}"
    )
    return {
        "size": size,
        "catch_copy": title,
        "sub_copy": body,
        "layout": layout,
        "font_spec": font_spec,
        "output_filename": filename,
        "prompt": prompt,
    }


def _video_prompt_item(
    plan_item: dict,
    size: str,
    duration: str,
    filename: str,
    vertical: bool,
    brand_name: str,
) -> dict:
    scene_lines = []
    for index, raw_scene in enumerate(plan_item.get("scenes", []), 1):
        scene = raw_scene if isinstance(raw_scene, dict) else {}
        heading = _plain_text(scene.get("caption", ""), 22)
        telop_text = _plain_text(scene.get("narration", ""), 120)
        visual = _plain_text(scene.get("visual") or scene.get("direction", ""), 100)
        scene_lines.append(
            f"シーン{index}（4〜6秒を目安）：上部見出し『{heading}』。"
            f"音声にせずタイピング風に表示するテロップ本文『{telop_text}』。"
            f"このシーンが担当する記事の要点は『{heading}。{telop_text}』。"
            f"イラストは『{visual or telop_text}』を表す具体的な人物・表情・視線・動作・背景・小物。"
            "見出し、テロップ、イラストを同じ要点に一致させ、内容と無関係な汎用場面にしない。"
        )
    scene_script = " ".join(scene_lines)
    if vertical:
        layout = "上部コピー帯20％・中央メイン映像55％・下部テロップ帯10％・右端と最下部の操作UI用安全余白15％"
        font_spec = "太めの日本語ゴシック体。表紙メイン96〜120px、表紙サブはメインの約80％、場面見出し72〜88px、下部補足は見出しの約80％、最大2行、行間1.25〜1.4倍"
        cta = "最後の3〜4秒は、記事内で確認できる次の行動を自然に案内し、必要に応じてプロフィールのリンクへ誘導する"
    else:
        layout = "人物・映像と文字を左右に分離し、下部に独立した字幕帯を設ける。重要要素は画面端から十分に離す"
        font_spec = "太めの日本語ゴシック体。表紙メイン88〜112px、表紙サブはメインの約80％、場面見出し64〜80px、下部補足は見出しの約80％、最大2行、行間1.25〜1.4倍"
        cta = "最後の3〜4秒は、記事内で確認できる次の行動を自然に案内し、必要に応じて概要欄のリンクへ誘導する"
    brand = _plain_text(brand_name, 30)
    brand_rule = f"ブランド名『{brand}』は必要な場合のみ控えめに表示する。" if brand else ""
    prompt = (
        "各フレームを映像表示エリアとテロップ専用エリアへ完全分離する。"
        "あなたは読者心理と視聴維持を熟知したプロのマーケティングコンサルタントであり、"
        "プロのイラストレーター兼映像ディレクターである。情報の優先順位と視線誘導を設計した、求心力のある高品質なイラスト動画を制作する。"
        f"{BRIGHT_VISUAL_RULES}{CONTENT_VISUAL_RULES}"
        f"出力は{size}、長さは{duration}。{layout}。全フレームで境界を固定し、文字・帯・字幕を映像領域へ越境させない。"
        "再生開始0.0秒の最初のフレームから、完成した表紙イラストと短いキャッチコピーを明るく鮮明に表示する。"
        "冒頭の黒画面、空白画面、無地背景、読み込み待ち、暗転、黒からのフェードインを一切入れない。"
        "表紙は3.5〜4秒間表示する。最初の0.5秒以内に完成した表紙を表示し、視聴者がキャッチコピーとイラストを落ち着いて読める時間を確保する。"
        f"{font_spec}。上部は場面見出し、下部は具体的な補足説明とし、同じ文章を上下へ重複表示しない。"
        "下部の補足（サブテキスト）のフォントサイズは、上部の見出し（メインテキスト）の約80％に統一する。"
        f"すべての画面テキストは日本語にする。{TEXT_LAYOUT_RULES}"
        "動画全体で完成記事の重要点を順番に要約する。冒頭で読者の悩みや関心を示し、中盤で原因・知識・手順などの主要点、"
        "終盤で得られる理解や次の行動を示す。各シーンは記事の異なる要点を1つずつ担当し、同じ内容や似た構図を繰り返さない。"
        "同じ主人公、画風、色設計を保ちながら、場面ごとに表情、動作、背景、小物、カメラ距離を変え、一続きの物語として見せる。"
        f"場面構成：{scene_script} "
        "人の声、音声ナレーション、読み上げ音声、会話音声は一切入れない。元のnarration欄の文章はすべて画面テロップとして使用する。"
        "テロップ本文は、パソコンやスマートフォンで文字を入力しているように、左から右へ1文字ずつ現れるタイピング演出にする。"
        "1文字の表示間隔は0.04〜0.07秒を目安とし、1行を打ち終えた後は1.5〜2秒読める状態で保持する。点滅カーソルは控えめにし、読みにくい高速表示は禁止する。"
        "テロップは下部専用帯の中央へ配置し、人物の顔・手・身体、重要な小物、場面の主役と1ピクセルも重ねない。"
        "前のテロップが消えてから次のテロップが始まるまでの空白は最大0.2秒とし、場面転換は0.2〜0.4秒で行う。"
        "明るくポップで前向きな、著作権上利用可能なインストゥルメンタルBGMを0.0秒から入れる。"
        "メジャーキーの軽快なピアノ、ウクレレ、柔らかなギター、控えめな手拍子と軽いパーカッションを使い、親しみ・安心感・期待感が伝わる曲調にする。"
        "子ども向けすぎる音、騒がしい音、コミカルすぎる音、暗い・不安・悲しい・重い曲調は禁止する。"
        "BGMは場面転換中も途切れさせず、テロップのタイピング演出と映像の切り替えをリズムに合わせ、終了時だけ自然にフェードアウトする。"
        "意味のない静止、BGMの音切れ、冒頭の黒フレームは禁止し、問題があれば再生成する。"
        f"{cta}。{brand_rule} Instagram、YouTube、TikTok、X、FacebookなどのSNS名、SNSロゴ、アプリアイコン、"
        "ユーザー名、保存ファイル名、拡張子、透かしを画面に表示しない。不自然な身体変形、激しい点滅、過剰な動きを避ける。"
        "映像の検品では、全フレームを確認し、上下テキストの重複、タイピング順序、読める保持時間、文字の欠落、"
        "テロップと人物・イラストの重なり、安全余白、場面転換、音声ナレーションが混入していないこと、BGMの明るさと音切れも確認する。"
        f"{PROFESSIONAL_REVIEW}"
    )
    return {
        "size": size,
        "duration": duration,
        "layout": layout,
        "font_spec": font_spec,
        "output_filename": filename,
        "prompt": prompt,
    }


def _build_creative_prompts(plan: dict, article: str, brand_name: str) -> dict:
    x_data, facebook = plan.get("x_image", {}), plan.get("facebook", {})
    threads, gbp = plan.get("threads", {}), plan.get("gbp", {})
    reel, youtube, tiktok = plan.get("reel", {}), plan.get("youtube", {}), plan.get("tiktok", {})
    horizontal = "左側35％をテキスト専用、右側65％をイラスト専用とする左右分割。背景色と余白で境界を明確にする"
    square = "上部25％を見出し、中央55％をイラスト、下部20％を補足専用カードとして3領域を完全分離する"
    vertical = "上部20％を見出し、中央60％をイラスト、下部5％を補足、残り15％を操作UI用安全余白として固定する"
    prompts = {
        "x_image": _image_prompt_item(x_data.get("title", ""), x_data.get("body", ""), "1200×675", horizontal, "太めゴシック。見出し56〜72px、補足は見出しの約80％、行間1.25〜1.4倍", MEDIA_FILENAMES["x_image"], x_data.get("visual", "")),
        "facebook_eyecatch": _image_prompt_item(facebook.get("image_title", ""), facebook.get("image_body", ""), "1200×630", horizontal, "太めゴシック。見出し56〜72px、補足は見出しの約80％、行間1.25〜1.4倍", MEDIA_FILENAMES["facebook_eyecatch"], facebook.get("visual", "")),
        "gbp_image": _image_prompt_item(gbp.get("image_title", ""), gbp.get("image_body", ""), "1200×900", horizontal, "太めゴシック。見出し64〜82px、補足は見出しの約80％、行間1.25〜1.4倍", MEDIA_FILENAMES["gbp_image"], gbp.get("visual", "")),
        "threads_image": _image_prompt_item(threads.get("image_title", ""), threads.get("image_body", ""), "1080×1080", square, "太めゴシック。見出し64〜80px、補足は見出しの約80％、行間1.25〜1.4倍", MEDIA_FILENAMES["threads_image"], threads.get("visual", "")),
        "reel_cover": _image_prompt_item(reel.get("cover_title", ""), reel.get("cover_body", ""), "1080×1920", vertical, "太めゴシック。見出し72〜96px、補足は見出しの約80％、最大2行", MEDIA_FILENAMES["reel_cover"], _first_scene_visual(reel)),
        "youtube_thumbnail": _image_prompt_item(youtube.get("thumbnail_title", ""), youtube.get("thumbnail_body", ""), "1280×720", horizontal, "太めゴシック。見出し80〜110px、補足は見出しの約80％、最大2行", MEDIA_FILENAMES["youtube_thumbnail"], _first_scene_visual(youtube)),
        "tiktok_cover": _image_prompt_item(tiktok.get("cover_title", ""), tiktok.get("cover_body", ""), "1080×1920", vertical, "太めゴシック。見出し72〜96px、補足は見出しの約80％、最大2行", MEDIA_FILENAMES["tiktok_cover"], _first_scene_visual(tiktok)),
        "reel_video": _video_prompt_item(reel, "1080×1920", "40〜45秒", MEDIA_FILENAMES["reel_video"], True, brand_name),
        "youtube_video": _video_prompt_item(youtube, "1920×1080", "40〜45秒", MEDIA_FILENAMES["youtube_video"], False, brand_name),
        "tiktok_video": _video_prompt_item(tiktok, "1080×1920", "40〜45秒", MEDIA_FILENAMES["tiktok_video"], True, brand_name),
    }
    prompts["instagram_carousel"] = []
    for index, slide in enumerate(plan.get("carousel", {}).get("slides", [])[:9], 1):
        item = _image_prompt_item(
            slide.get("title", ""), slide.get("body", ""), "1080×1350",
            "上部18％を見出し、中央57％をイラスト、下部25％を説明カードとして固定し、3領域を完全分離する",
            "太めゴシック。大見出し64〜80px、説明は大見出しの約80％、最大4行、行間1.25〜1.4倍",
            f"Instagram_カルーセル_{index:02d}.png",
            slide.get("visual", ""),
        )
        item["slide"] = index
        prompts["instagram_carousel"].append(item)
    sections = _article_image_sections(article, maximum=6) or [{
        "level": "H2", "heading": "記事のポイント",
        "summary": _plain_text(article, 140) or "記事の要点を視覚的に分かりやすく表現する",
    }]
    prompts["article_section_images"] = []
    for index, section in enumerate(sections, 1):
        item = _image_prompt_item(
            section.get("heading", ""), section.get("summary", ""), "1200×675", horizontal,
            "太めゴシック。見出し56〜72px、補足は見出しの約80％、1行15〜18文字以内、行間1.25〜1.4倍",
            f"ブログ_{section.get('level', 'H2')}_{index:02d}_{_safe_filename_part(section.get('heading', ''))}.png",
            f"記事の{section.get('level', 'H2')}『{section.get('heading', '')}』。要点：{section.get('summary', '')}",
        )
        item.update({"section": index, "heading_level": section.get("level", "H2"), "heading": section.get("heading", "")})
        prompts["article_section_images"].append(item)
    return prompts


def _validate_social_plan(data: dict) -> None:
    required = ("x_posts", "threads", "facebook", "gbp", "carousel", "reel", "youtube", "tiktok", "creative_prompts")
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"SNS構成に必要な項目が不足しています：{', '.join(missing)}")
    if len(data.get("carousel", {}).get("slides", [])) != 9:
        raise ValueError("カルーセル構成が9枚ではありません。")
    for key in ("reel", "youtube", "tiktok"):
        if not data.get(key, {}).get("scenes"):
            raise ValueError(f"{key}の動画構成がありません。")
    prompts = data.get("creative_prompts", {})
    required_prompts = (
        "x_image", "facebook_eyecatch", "gbp_image", "threads_image", "reel_cover",
        "reel_video", "youtube_thumbnail", "youtube_video", "tiktok_cover",
        "tiktok_video", "instagram_carousel", "article_section_images",
    )
    if any(key not in prompts for key in required_prompts):
        raise ValueError("画像・動画制作用プロンプトが不足しています。")


def generate_social_plan(client, model: str, article: str, call_llm, brand_name: str = "") -> dict:
    prompt = f"""【完成記事からSNS投稿文・動画台本を作成】
あなたは、読者心理・購買行動・媒体特性を熟知したプロのマーケティングコンサルタントであり、
広告・出版分野で経験豊富なプロのイラストレーター兼映像ディレクターです。
以下の完成記事だけを情報源として、各SNS向けコンテンツをJSONで作成してください。

完成記事：
---
{article}
---

厳格な条件：
- 記事にない数値、実績、料金、資格、口コミ、効果、人物、店舗情報、研究結果を追加しない
- 医療・健康情報を断定しない
- 同じ文章を使い回さず、媒体ごとに最適化する
- ハッシュタグは文字列配列にする
- カルーセルは必ず9枚。1枚目は表紙、9枚目はまとめ・自然な行動喚起
- カルーセル9枚だけで完成記事の要点を順序よく理解できる構成にする。2枚目で読者の悩み・現状、3〜8枚目で原因・知識・方法・注意点・変化など記事の主要点を重複なく割り当てる
- カルーセル各枚のtitle、body、visualは必ず同じ記事要点を表す。全9枚で同じ主人公・画風・色設計を保ち、表情、動作、背景、小物、構図は各要点に合わせて変える
- リール、TikTok、YouTubeはいずれも40〜45秒程度。各動画は5〜7シーン、1シーン4〜6秒を目安にする
- 動画は完成記事を短く要約する。冒頭は読者の悩みまたは関心、中盤は記事の主要点、終盤はまとめと次の行動にし、各シーンへ異なる記事要点を1つずつ割り当てる
- 動画各シーンのcaption、narration、visualは必ず同じ記事要点を表し、記事と無関係な汎用場面や同じ構図の繰り返しを避ける
- 人の声や音声ナレーションは使用しない。narration欄には、動画内でタイピング風に表示する日本語テロップ本文を入れる
- テロップ本文は1シーンで読み切れる45文字以内の短文にし、見出しと同じ文章を繰り返さない
- テロップ間の空白を最大0.2秒にできる構成とし、不要な間や長い余韻を作らない
- 動画のcaptionは上部に表示する短い場面見出し、narrationは読み上げる自然な文章
- 上部見出しと下部テロップへ同じ文章を重複させない
- 画面テキストは日本語の文節と意味のまとまりで自然に改行できる長さにする。単語途中の分割、助詞・句読点の行頭、1文字だけの行を避ける
- 改行後は各行の見た目の長さが近くなり、中央揃えで視覚的な重心が偏らない短文にする
- visualは人物、表情、視線、動作、場所、背景、小物、光、記事要点との関係が分かる具体的な日本語の場面説明。単なる「笑顔の人物」「学んでいる人」だけにしない
- visualは明るいハイキー光と清潔感のある魅力的な配色を基本にしつつ、記事内容に合う場面を描く。記事にない事実や効果を絵で追加しない
- JSONを途中で省略せず、次の形式以外は出力しない

{{
  "x_posts": [
    {{"text": "投稿文", "hashtags": ["#タグ"]}},
    {{"text": "別角度の投稿文", "hashtags": ["#タグ"]}},
    {{"text": "別角度の投稿文", "hashtags": ["#タグ"]}}
  ],
  "x_image": {{"title": "短い見出し", "body": "60文字以内の説明", "visual": "具体的な場面"}},
  "threads": {{"text": "投稿文", "hashtags": ["#タグ"], "image_title": "短い見出し", "image_body": "60文字以内", "visual": "具体的な場面"}},
  "facebook": {{"text": "詳しい投稿文", "hashtags": ["#タグ"], "image_title": "短い見出し", "image_body": "60文字以内", "visual": "具体的な場面"}},
  "gbp": {{"text": "GBP最新情報の投稿文", "image_title": "短い見出し", "image_body": "80文字以内", "visual": "具体的な場面"}},
  "carousel": {{"caption": "Instagramキャプション", "hashtags": ["#タグ"], "slides": [{{"title": "短い見出し", "body": "80文字以内", "visual": "具体的な場面"}}]}},
  "reel": {{"caption": "リール投稿文", "hashtags": ["#タグ"], "cover_title": "表紙見出し", "cover_body": "短い補足", "scenes": [{{"caption": "上部見出し", "narration": "音声にせずタイピング表示する45文字以内のテロップ本文", "visual": "具体的な場面"}}]}},
  "youtube": {{"title": "タイトル", "description": "概要欄", "hashtags": ["#タグ"], "thumbnail_title": "サムネイル見出し", "thumbnail_body": "短い補足", "scenes": [{{"caption": "上部見出し", "narration": "音声にせずタイピング表示する45文字以内のテロップ本文", "visual": "具体的な場面"}}]}},
  "tiktok": {{"caption": "投稿文", "hashtags": ["#タグ"], "cover_title": "表紙見出し", "cover_body": "短い補足", "scenes": [{{"caption": "上部見出し", "narration": "音声にせずタイピング表示する45文字以内のテロップ本文", "visual": "具体的な場面"}}]}}
}}"""
    last_error = None
    for attempt in range(2):
        retry = "" if not attempt else "\n前回はJSONが不完全でした。文章量を調整し、必ず最後まで有効なJSONで出力してください。"
        raw = call_llm(
            client, model, prompt + retry, 16_000,
            response_mime_type="application/json", temperature=0.35,
        )
        try:
            data = _normalize_plan(_load_json_response(raw), article)
            data["creative_prompts"] = _build_creative_prompts(data, article, brand_name)
            _validate_social_plan(data)
            return data
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = exc
    raise ValueError(f"SNS投稿文と制作プロンプトを完成できませんでした：{last_error}")


def _hashtags(value) -> str:
    return " ".join(str(tag) for tag in value) if isinstance(value, list) else str(value or "")


def social_text(plan: dict) -> str:
    parts = ["X（旧Twitter）投稿案"]
    for index, post in enumerate(plan.get("x_posts", []), 1):
        parts.append(f"\n【パターン{index}】\n{post.get('text', '')}\n{_hashtags(post.get('hashtags'))}")
    for key, label in (("threads", "Threads"), ("facebook", "Facebook"), ("gbp", "Googleビジネスプロフィール")):
        item = plan.get(key, {})
        parts.append(f"\n\n{label}投稿\n{item.get('text', '')}\n{_hashtags(item.get('hashtags'))}")
    carousel = plan.get("carousel", {})
    parts.append(f"\n\nInstagram投稿\n{carousel.get('caption', '')}\n{_hashtags(carousel.get('hashtags'))}")
    for key, label in (("reel", "Instagramリール"), ("youtube", "YouTube"), ("tiktok", "TikTok")):
        item = plan.get(key, {})
        parts.append(f"\n\n{label}\n{item.get('title', '')}\n{item.get('caption', item.get('description', ''))}\n{_hashtags(item.get('hashtags'))}")
    return "\n".join(parts).strip()


def creative_prompt_text(plan: dict) -> str:
    prompts = plan.get("creative_prompts", {})
    labels = (
        ("x_image", "X投稿画像"),
        ("facebook_eyecatch", "Facebookアイキャッチ"),
        ("gbp_image", "Googleビジネスプロフィール投稿画像"),
        ("threads_image", "Threads投稿画像"),
        ("reel_cover", "Instagramリール表紙"),
        ("reel_video", "Instagramリール動画"),
        ("youtube_thumbnail", "YouTubeサムネイル"),
        ("youtube_video", "YouTube動画"),
        ("tiktok_cover", "TikTok表紙"),
        ("tiktok_video", "TikTok動画"),
    )
    parts = ["# 画像・動画制作用プロンプト"]
    for key, label in labels:
        item = prompts.get(key, {})
        parts.append(
            f"\n\n## {label}\nサイズ：{item.get('size', '')}\n"
            f"推奨保存ファイル名：{item.get('output_filename', '')}\n"
            f"画像内キャッチコピー：{item.get('catch_copy', '')}\n"
            f"画像内補足：{item.get('sub_copy', '')}\n"
            f"レイアウト：{item.get('layout', '')}\n"
            f"フォント指定：{item.get('font_spec', '')}\n\n{item.get('prompt', '')}"
        )
    parts.append("\n\n## Instagramカルーセル9枚")
    for item in prompts.get("instagram_carousel", []):
        parts.append(
            f"\n\n### {item.get('slide', '')}枚目\nサイズ：{item.get('size', '')}\n"
            f"推奨保存ファイル名：{item.get('output_filename', '')}\n"
            f"画像内見出し：{item.get('catch_copy', '')}\n画像内説明：{item.get('sub_copy', '')}\n"
            f"レイアウト：{item.get('layout', '')}\nフォント指定：{item.get('font_spec', '')}\n\n{item.get('prompt', '')}"
        )
    parts.append("\n\n## ブログ記事内で使うセクション画像")
    for item in prompts.get("article_section_images", []):
        parts.append(
            f"\n\n### セクション{item.get('section', '')}｜{item.get('heading_level', '')}：{item.get('heading', '')}\n"
            f"サイズ：{item.get('size', '')}\n推奨保存ファイル名：{item.get('output_filename', '')}\n"
            f"画像内見出し：{item.get('catch_copy', '')}\n画像内補足：{item.get('sub_copy', '')}\n"
            f"レイアウト：{item.get('layout', '')}\nフォント指定：{item.get('font_spec', '')}\n\n{item.get('prompt', '')}"
        )
    return "".join(parts).strip()

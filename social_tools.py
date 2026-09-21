import base64
import io
import json
import math
import re
import subprocess
import tempfile
import wave
import zipfile
from pathlib import Path
from typing import Callable

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont


TTS_MODEL = "gemini-3.1-flash-tts-preview"
SAMPLE_RATE = 24_000


def _strip_code_fence(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def generate_social_plan(client, model: str, article: str, call_llm) -> dict:
    prompt = f"""【完成記事からSNS展開素材を作成】
以下の完成記事だけを情報源として、各SNS向けコンテンツを作成してください。

完成記事：
---
{article}
---

厳格な条件：
- 記事にない数値、実績、料金、資格、口コミ、効果、人物、店舗情報、研究結果を追加しない
- 医療・健康情報を断定しない
- 同じ文章の使い回しを避け、媒体ごとに最適化する
- ハッシュタグは文字列配列にする
- カルーセルは必ず9枚。1枚目は表紙、9枚目はまとめ・行動喚起
- リールとTikTokは45〜60秒程度の日本語ナレーション
- YouTubeは3〜5分程度の日本語ナレーション
- 動画のcaptionは画面に表示する短文、narrationは読み上げる自然な文章
- 次のJSON以外は一切出力しない

JSON形式：
{{
  "x_posts": [
    {{"text": "投稿文", "hashtags": ["#タグ"]}},
    {{"text": "別角度の投稿文", "hashtags": ["#タグ"]}},
    {{"text": "別角度の投稿文", "hashtags": ["#タグ"]}}
  ],
  "x_image": {{"title": "X投稿画像の見出し", "body": "60文字以内の説明"}},
  "threads": {{
    "text": "少し長めの投稿文",
    "hashtags": ["#タグ"],
    "image_title": "Threads画像の見出し",
    "image_body": "60文字以内の説明"
  }},
  "facebook": {{
    "text": "信頼感のある詳しい投稿文",
    "hashtags": ["#タグ"],
    "image_title": "画像に表示する短い見出し",
    "image_body": "画像に表示する60文字以内の説明"
  }},
  "gbp": {{
    "text": "Googleビジネスプロフィール最新情報の投稿文",
    "image_title": "GBP画像の短い見出し",
    "image_body": "80文字以内の説明"
  }},
  "carousel": {{
    "caption": "Instagramキャプション",
    "hashtags": ["#タグ"],
    "slides": [{{"title": "短い見出し", "body": "80文字以内の本文"}}]
  }},
  "reel": {{
    "caption": "Instagramリールキャプション",
    "hashtags": ["#タグ"],
    "cover_title": "リール表紙の短い見出し",
    "cover_body": "短い補足",
    "scenes": [{{"caption": "画面表示20文字以内", "narration": "読み上げ文"}}]
  }},
  "youtube": {{
    "title": "YouTubeタイトル",
    "description": "概要欄",
    "hashtags": ["#タグ"],
    "thumbnail_title": "サムネイルの短い見出し",
    "thumbnail_body": "短い補足",
    "scenes": [{{"caption": "画面見出し", "narration": "読み上げ文"}}]
  }},
  "tiktok": {{
    "caption": "TikTokキャプション",
    "hashtags": ["#タグ"],
    "cover_title": "TikTok表紙の短い見出し",
    "cover_body": "短い補足",
    "scenes": [{{"caption": "画面表示20文字以内", "narration": "読み上げ文"}}]
  }}
}}"""
    raw = call_llm(client, model, prompt, 9000)
    data = json.loads(_strip_code_fence(raw))
    if len(data.get("carousel", {}).get("slides", [])) != 9:
        raise ValueError("カルーセル構成を9枚で生成できませんでした。もう一度お試しください。")
    for key in ("reel", "youtube", "tiktok"):
        if not data.get(key, {}).get("scenes"):
            raise ValueError(f"{key}の動画構成を生成できませんでした。")
    return data


def _font_path() -> str:
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansJP-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/YuGothM.ttc",
        "C:/Windows/Fonts/meiryo.ttc",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    raise RuntimeError("日本語フォントが見つかりません。packages.txtの設定を確認してください。")


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(_font_path(), size=size)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text.replace("\n", " "):
        candidate = current + char
        if current and draw.textlength(candidate, font=font) > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _gradient(width: int, height: int, top=(239, 250, 247), bottom=(211, 238, 231)) -> Image.Image:
    ratio = np.linspace(0, 1, height, dtype=np.float32)[:, None, None]
    top_color = np.array(top, dtype=np.float32)[None, None, :]
    bottom_color = np.array(bottom, dtype=np.float32)[None, None, :]
    rows = top_color * (1 - ratio) + bottom_color * ratio
    pixels = np.repeat(rows.astype(np.uint8), width, axis=1)
    return Image.fromarray(pixels, mode="RGB")


def render_card(
    title: str,
    body: str,
    width: int,
    height: int,
    index: int,
    total: int,
    brand_name: str,
) -> Image.Image:
    image = _gradient(width, height)
    draw = ImageDraw.Draw(image)
    margin = int(width * 0.07)
    accent = (42, 125, 110)
    dark = (31, 55, 50)
    white = (255, 255, 255)
    draw.rounded_rectangle(
        (margin, margin, width - margin, height - margin),
        radius=max(28, width // 28),
        fill=(255, 255, 255),
        outline=(184, 220, 211),
        width=max(3, width // 300),
    )
    draw.rounded_rectangle(
        (margin, margin, width - margin, margin + int(height * 0.035)),
        radius=18,
        fill=accent,
    )
    title_font = _font(max(44, width // 17))
    body_font = _font(max(30, width // 27))
    small_font = _font(max(22, width // 42))
    usable_width = width - margin * 4
    title_lines = _wrap(draw, title, title_font, usable_width)[:4]
    title_y = margin + int(height * 0.12)
    for line in title_lines:
        box = draw.textbbox((0, 0), line, font=title_font)
        line_width = box[2] - box[0]
        draw.text(((width - line_width) / 2, title_y), line, fill=accent, font=title_font)
        title_y += int(title_font.size * 1.35)

    divider_y = title_y + int(height * 0.035)
    draw.line((margin * 2, divider_y, width - margin * 2, divider_y), fill=(207, 226, 221), width=3)
    body_lines = _wrap(draw, body, body_font, usable_width)[:10]
    body_y = divider_y + int(height * 0.055)
    for line in body_lines:
        box = draw.textbbox((0, 0), line, font=body_font)
        line_width = box[2] - box[0]
        draw.text(((width - line_width) / 2, body_y), line, fill=dark, font=body_font)
        body_y += int(body_font.size * 1.55)

    if total == 1:
        footer = brand_name
    else:
        footer = f"{brand_name}   {index}/{total}" if brand_name else f"{index}/{total}"
    draw.text((margin * 1.6, height - margin * 1.65), footer, fill=(86, 116, 109), font=small_font)
    if total > 1:
        draw.ellipse(
            (width - margin * 2.1, height - margin * 1.9, width - margin * 1.45, height - margin * 1.25),
            fill=accent,
        )
        draw.text(
            (width - margin * 1.94, height - margin * 1.86),
            "›",
            fill=white,
            font=small_font,
        )
    return image


def _image_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def build_carousel(slides: list[dict], brand_name: str) -> tuple[list[bytes], bytes]:
    images = []
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for index, slide in enumerate(slides, start=1):
            image = render_card(
                slide.get("title", ""),
                slide.get("body", ""),
                1080,
                1080,
                index,
                len(slides),
                brand_name,
            )
            data = _image_bytes(image)
            images.append(data)
            archive.writestr(f"carousel_{index:02d}.png", data)
    return images, zip_buffer.getvalue()


def build_facebook_image(facebook: dict, brand_name: str) -> bytes:
    image = render_card(
        facebook.get("image_title", ""),
        facebook.get("image_body", ""),
        1200,
        630,
        1,
        1,
        brand_name,
    )
    return _image_bytes(image)


def build_platform_image(
    title: str,
    body: str,
    width: int,
    height: int,
    brand_name: str,
) -> bytes:
    return _image_bytes(render_card(title, body, width, height, 1, 1, brand_name))


def _tts_pcm(client, narration: str, voice: str) -> bytes:
    prompt = (
        "次の日本語原稿を、聞き取りやすく、やさしく信頼感のある自然な速度で、"
        "文章を追加・省略せずに読み上げてください。\n\n" + narration
    )
    interaction = client.interactions.create(
        model=TTS_MODEL,
        input=prompt,
        response_format={"type": "audio"},
        generation_config={"speech_config": [{"voice": voice}]},
    )
    audio = interaction.output_audio
    if not audio or not audio.data:
        raise RuntimeError("ナレーション音声を生成できませんでした。")
    # google-genai 2.xでは音声データがBase64文字列として返ります。
    # 将来のSDK差異でbytesが返る場合も、そのまま受け取れるようにします。
    if isinstance(audio.data, bytes):
        return audio.data
    return base64.b64decode(audio.data)


def _write_wave(path: Path, pcm: bytes) -> float:
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm)
    return len(pcm) / (SAMPLE_RATE * 2)


def _write_bgm(path: Path, duration: float) -> None:
    frame_count = max(1, int(duration * SAMPLE_RATE))
    t = np.arange(frame_count, dtype=np.float64) / SAMPLE_RATE
    chord = (
        np.sin(2 * math.pi * 220.00 * t)
        + 0.7 * np.sin(2 * math.pi * 277.18 * t)
        + 0.55 * np.sin(2 * math.pi * 329.63 * t)
    ) / 2.25
    pulse = 0.65 + 0.35 * np.sin(2 * math.pi * 0.18 * t)
    fade = np.minimum(np.clip(t / 1.5, 0, 1), np.clip((duration - t) / 1.5, 0, 1))
    samples = np.int16(np.clip(chord * pulse * fade * 0.18, -1, 1) * 32767)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(samples.tobytes())


def _safe_concat_path(path: Path) -> str:
    return str(path).replace("'", "'\\''")


def build_video(
    client,
    scenes: list[dict],
    width: int,
    height: int,
    brand_name: str,
    voice: str,
    output_name: str,
) -> bytes:
    narration_parts = [scene.get("narration", "").strip() for scene in scenes]
    narration = "\n".join(part for part in narration_parts if part)
    if not narration:
        raise ValueError("ナレーション原稿がありません。")
    pcm = _tts_pcm(client, narration, voice)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        narration_path = tmp_dir / "narration.wav"
        bgm_path = tmp_dir / "bgm.wav"
        output_path = tmp_dir / output_name
        duration = max(_write_wave(narration_path, pcm), len(scenes) * 2.0)
        _write_bgm(bgm_path, duration)

        weights = [max(1, len(text)) for text in narration_parts]
        weight_total = sum(weights)
        durations = [max(1.8, duration * weight / weight_total) for weight in weights]
        duration_scale = duration / sum(durations)
        durations = [value * duration_scale for value in durations]

        concat_lines = []
        for index, (scene, scene_duration) in enumerate(zip(scenes, durations), start=1):
            frame_path = tmp_dir / f"frame_{index:02d}.png"
            image = render_card(
                scene.get("caption", ""),
                "",
                width,
                height,
                index,
                len(scenes),
                brand_name,
            )
            image.save(frame_path, "PNG")
            concat_lines.append(f"file '{_safe_concat_path(frame_path)}'")
            concat_lines.append(f"duration {scene_duration:.3f}")
        concat_lines.append(f"file '{_safe_concat_path(tmp_dir / f'frame_{len(scenes):02d}.png')}'")
        concat_path = tmp_dir / "frames.txt"
        concat_path.write_text("\n".join(concat_lines), encoding="utf-8")

        command = [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_path),
            "-i",
            str(narration_path),
            "-i",
            str(bgm_path),
            "-filter_complex",
            "[1:a]volume=1.0[a1];[2:a]volume=0.16[a2];[a1][a2]amix=inputs=2:duration=first[a]",
            "-map",
            "0:v:0",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=420)
        if completed.returncode != 0:
            raise RuntimeError(f"動画変換に失敗しました：{completed.stderr[-500:]}")
        return output_path.read_bytes()


def _social_text(plan: dict) -> str:
    parts = ["X（旧Twitter）投稿案"]
    for index, post in enumerate(plan.get("x_posts", []), start=1):
        parts.append(
            f"\n【パターン{index}】\n{post.get('text', '')}\n{' '.join(post.get('hashtags', []))}"
        )
    threads = plan.get("threads", {})
    parts.append(
        f"\n\nThreads投稿\n{threads.get('text', '')}\n{' '.join(threads.get('hashtags', []))}"
    )
    facebook = plan.get("facebook", {})
    parts.append(
        f"\n\nFacebook投稿\n{facebook.get('text', '')}\n{' '.join(facebook.get('hashtags', []))}"
    )
    gbp = plan.get("gbp", {})
    parts.append(f"\n\nGoogleビジネスプロフィール投稿\n{gbp.get('text', '')}")
    carousel = plan.get("carousel", {})
    parts.append(
        f"\n\nInstagramカルーセル キャプション\n{carousel.get('caption', '')}\n{' '.join(carousel.get('hashtags', []))}"
    )
    for key, label in (("reel", "Instagramリール"), ("youtube", "YouTube"), ("tiktok", "TikTok")):
        item = plan.get(key, {})
        parts.append(
            f"\n\n{label}\n{item.get('title', '')}\n{item.get('caption', item.get('description', ''))}\n{' '.join(item.get('hashtags', []))}"
        )
    return "\n".join(parts).strip()


def social_text(plan: dict) -> str:
    return _social_text(plan)


def build_media_package(
    client,
    plan: dict,
    brand_name: str,
    voice: str,
    progress: Callable[[str], None],
) -> dict[str, bytes]:
    progress("9枚のカルーセル画像を作成しています…")
    carousel_images, carousel_zip = build_carousel(plan["carousel"]["slides"], brand_name)
    progress("Facebook投稿画像を作成しています…")
    facebook_image = build_facebook_image(plan.get("facebook", {}), brand_name)
    progress("各SNSの投稿画像・表紙・サムネイルを作成しています…")
    x_image_data = plan.get("x_image", {})
    x_image = build_platform_image(
        x_image_data.get("title", ""), x_image_data.get("body", ""), 1200, 675, brand_name
    )
    threads = plan.get("threads", {})
    threads_image = build_platform_image(
        threads.get("image_title", ""), threads.get("image_body", ""), 1080, 1080, brand_name
    )
    gbp = plan.get("gbp", {})
    gbp_image = build_platform_image(
        gbp.get("image_title", ""), gbp.get("image_body", ""), 1200, 900, brand_name
    )
    reel = plan.get("reel", {})
    reel_cover = build_platform_image(
        reel.get("cover_title", ""), reel.get("cover_body", ""), 1080, 1920, brand_name
    )
    youtube = plan.get("youtube", {})
    youtube_thumbnail = build_platform_image(
        youtube.get("thumbnail_title", ""),
        youtube.get("thumbnail_body", ""),
        1280,
        720,
        brand_name,
    )
    tiktok = plan.get("tiktok", {})
    tiktok_cover = build_platform_image(
        tiktok.get("cover_title", ""), tiktok.get("cover_body", ""), 1080, 1920, brand_name
    )
    progress("Instagramリール動画のナレーションとMP4を作成しています…")
    reel_video = build_video(
        client, plan["reel"]["scenes"], 1080, 1920, brand_name, voice, "instagram_reel.mp4"
    )
    progress("YouTube動画のナレーションとMP4を作成しています…")
    youtube_video = build_video(
        client, plan["youtube"]["scenes"], 1920, 1080, brand_name, voice, "youtube_video.mp4"
    )
    progress("TikTok動画のナレーションとMP4を作成しています…")
    tiktok_video = build_video(
        client, plan["tiktok"]["scenes"], 1080, 1920, brand_name, voice, "tiktok_video.mp4"
    )

    text_data = _social_text(plan).encode("utf-8-sig")
    json_data = json.dumps(plan, ensure_ascii=False, indent=2).encode("utf-8")
    all_buffer = io.BytesIO()
    with zipfile.ZipFile(all_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("social_posts.txt", text_data)
        archive.writestr("social_plan.json", json_data)
        for index, image_data in enumerate(carousel_images, start=1):
            archive.writestr(f"carousel/carousel_{index:02d}.png", image_data)
        archive.writestr("images/facebook_post_1200x630.png", facebook_image)
        archive.writestr("images/x_post_1200x675.png", x_image)
        archive.writestr("images/threads_post_1080x1080.png", threads_image)
        archive.writestr("images/gbp_post_1200x900.png", gbp_image)
        archive.writestr("images/instagram_reel_cover_1080x1920.png", reel_cover)
        archive.writestr("images/youtube_thumbnail_1280x720.png", youtube_thumbnail)
        archive.writestr("images/tiktok_cover_1080x1920.png", tiktok_cover)
        archive.writestr("videos/instagram_reel.mp4", reel_video)
        archive.writestr("videos/youtube_video.mp4", youtube_video)
        archive.writestr("videos/tiktok_video.mp4", tiktok_video)
    return {
        "all_zip": all_buffer.getvalue(),
        "carousel_zip": carousel_zip,
        "facebook_image": facebook_image,
        "x_image": x_image,
        "threads_image": threads_image,
        "gbp_image": gbp_image,
        "reel_cover": reel_cover,
        "youtube_thumbnail": youtube_thumbnail,
        "tiktok_cover": tiktok_cover,
        "reel_video": reel_video,
        "youtube_video": youtube_video,
        "tiktok_video": tiktok_video,
        "social_text": text_data,
    }

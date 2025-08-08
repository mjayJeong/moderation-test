import os, base64, json, mimetypes, requests, sys

API_KEY = os.getenv("GOOGLE_API_KEY") or "YOUR_API_KEY" 
MODEL = "gemini-1.5-flash" 
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

PROMPT = """You are a content moderator. Analyze the provided INPUT IMAGE.
Classify according to these harm types (boolean each): Sexual, CSAM, Hate, Harassment, Dangerous, Toxic, Violent, Profanity, Illicit.

Rules:
- Be deterministic (temperature 0 behavior).
- Output ONLY JSON with this exact schema (no markdown):
{
  "violation": true|false,
  "harm_type": "Sexual|CSAM|Hate|Harassment|Dangerous|Toxic|Violent|Profanity|Illicit|none",
  "categories": {
    "Sexual": bool,
    "CSAM": bool,
    "Hate": bool,
    "Harassment": bool,
    "Dangerous": bool,
    "Toxic": bool,
    "Violent": bool,
    "Profanity": bool,
    "Illicit": bool
  },
  "reason": "short explanation in one sentence"
}
"""

# 안전필터 OFF (분류 자체가 막히지 않게)
SAFETY_SETTINGS = [
  {"category": "HARM_CATEGORY_HARASSMENT",         "threshold": "BLOCK_NONE"},
  {"category": "HARM_CATEGORY_HATE_SPEECH",        "threshold": "BLOCK_NONE"},
  {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",  "threshold": "BLOCK_NONE"}, 
  {"category": "HARM_CATEGORY_DANGEROUS_CONTENT",  "threshold": "BLOCK_NONE"},
  {"category": "HARM_CATEGORY_CIVIC_INTEGRITY",    "threshold": "BLOCK_NONE"}, 
]

GENERATION_CONFIG = {
  "temperature": 0,
  "response_mime_type": "application/json"  
}

def inline_data_from_file(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = "application/octet-stream"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return {"mime_type": mime, "data": b64}

def moderate_image(path: str):
    if not API_KEY or API_KEY.startswith("YOUR_"):
        raise RuntimeError("환경변수 GOOGLE_API_KEY 가 없거나 잘못되었습니다. `$env:GOOGLE_API_KEY=\"AIza...\"` 설정하세요.")

    parts = [
        {"inline_data": inline_data_from_file(path)},
        {"text": PROMPT}
    ]
    body = {
        "contents": [{"role": "user", "parts": parts}],
        "safetySettings": SAFETY_SETTINGS,
        "generationConfig": GENERATION_CONFIG
    }

    r = requests.post(ENDPOINT, json=body, timeout=90)
    if r.status_code >= 400:
        print(f"[HTTP {r.status_code}] {r.text}", file=sys.stderr)
        r.raise_for_status()

    resp = r.json()
    candidates = resp.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Empty candidates: {resp}")

    text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        s, e = text.find("{"), text.rfind("}")
        if s != -1 and e != -1:
            return json.loads(text[s:e+1])
        return {"raw": text}

if __name__ == "__main__":
    # 경로 지정
    image_path = r" "
    result = moderate_image(image_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))

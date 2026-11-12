from dotenv import load_dotenv; load_dotenv()
import os
from openai import OpenAI
c = OpenAI(base_url=os.environ["LLM_BASE_URL"], api_key=os.environ["OPENAI_API_KEY"], max_retries=0)
try:
    c.chat.completions.create(model="qwen/qwen3.8-27b", messages=[{"role": "user", "content": "oi"}], max_tokens=5)
    print("LIBERADO")
except Exception as e:
    print(str(e)[:600])
    h = getattr(getattr(e, "response", None), "headers", {})
    for k, v in h.items():
        if "ratelimit" in k.lower() or "retry" in k.lower():
            print(k, "=", v)

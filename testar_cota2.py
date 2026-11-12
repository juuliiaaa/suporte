from dotenv import load_dotenv; load_dotenv()
import os
from openai import OpenAI
c = OpenAI(base_url=os.environ["LLM_BASE_URL"], api_key=os.environ["OPENAI_API_KEY"], max_retries=0)
try:
    c.chat.completions.create(model="qwen/qwen3.8-27b", messages=[{"role": "user", "content": "oi " * 3000}], max_tokens=5)
    print("LIBERADO PARA ATENDIMENTO COMPLETO")
except Exception as e:
    print(str(e)[:700])

import requests
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from config import Config
import time

class AIClient:
    def __init__(self):
        self.api_key = Config.API_KEY
        self.base_url = Config.BASE_URL
        self.model = Config.MODEL_NAME

    @retry(
        stop=stop_after_attempt(Config.MAX_RETRIES),
        wait=wait_fixed(2),
        retry=retry_if_exception_type((requests.RequestException, ValueError))
    )
    def chat(self, messages):
        """
        messages: [{"role": "user", "content": "..."}]
        """
        url = f"{self.base_url}/responses"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 拼接 messages 成单条 input
        input_text = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            input_text += f"[{role}]: {content}\n"

        payload = {
            "model": self.model,
            "input": input_text,
            "temperature": Config.TEMPERATURE
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)

            if resp.status_code == 429:  # 速率限制
                print("⚠️ 遇到速率限制，等待后重试...")
                time.sleep(5)
                raise requests.RequestException("Rate limit exceeded")

            if resp.status_code != 200:
                raise ValueError(f"API请求失败: {resp.status_code} {resp.text}")

            try:
                data = resp.json()
            except:
                raise ValueError(f"API返回不是JSON: {resp.text}")

            # 云雾 API 返回 content 或 output[0].content
            if "content" in data:
                content = data["content"]
                # 如果content是列表，提取文本
                if isinstance(content, list):
                    if len(content) > 0 and isinstance(content[0], dict):
                        return content[0].get("text", str(content))
                    else:
                        return str(content)
                return content
            elif "output" in data and len(data["output"]) > 0:
                output_item = data["output"][0]
                if isinstance(output_item, dict):
                    return output_item.get("content", output_item.get("text", ""))
                else:
                    return str(output_item)
            else:
                return str(data)

        except requests.Timeout:
            raise ValueError("API请求超时")
        except requests.ConnectionError:
            raise ValueError("网络连接错误")

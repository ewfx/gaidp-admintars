import requests
from typing import Optional, Dict, Any

class DeepSeekAdapter:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.last_call_time = 0
        self.min_call_interval = 1  # seconds between calls
        
    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """Send prompt to DeepSeek via OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "YOUR_SITE_URL",  # Required by OpenRouter
            "X-Title": "Banking Compliance App",  # Optional but recommended
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek/deepseek-chat-v3-0324:free",  # Full model name for OpenRouter
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30  # Add timeout
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse response
            print("In deepseek_adapter.py")
            print("#################################################")
            result = response.json()
            print("result: ", result)
            if result["choices"][0]["message"].get("content", "").strip():
                return result["choices"][0]["message"]["content"]
            else:
                return result["choices"][0]["message"]["reasoning"]
        except requests.exceptions.HTTPError as http_err:
            error_msg = f"HTTP error: {http_err}"
            if response and response.text:
                error_msg += f" | Response: {response.text}"
            raise Exception(error_msg)
        except Exception as e:
            raise Exception(f"API request failed: {str(e)}")
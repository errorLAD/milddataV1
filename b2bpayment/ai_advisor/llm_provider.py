import json
import urllib.request
import urllib.error

def call_llm_api(business_settings, system_prompt, user_prompt, temperature=0.2):
    """
    Invokes external LLM REST API (Google Gemini / OpenAI ChatGPT / Custom Endpoint).
    Returns generated response text string.
    Raises Exception if API call fails or is unconfigured.
    """
    if not business_settings or not business_settings.ai_api_key:
        raise ValueError("AI API Key is not configured in Business Settings.")

    provider = business_settings.ai_provider
    api_key = business_settings.ai_api_key.strip()
    model_name = business_settings.ai_model_name.strip() or ('gemini-1.5-flash' if provider == 'gemini' else 'gpt-4o-mini')
    temp = temperature or business_settings.ai_temperature or 0.2

    if provider == 'gemini':
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        
        full_text = f"{system_prompt}\n\nUSER PROMPT:\n{user_prompt}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": full_text}]
                }
            ],
            "generationConfig": {
                "temperature": temp
            }
        }
        
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['candidates'][0]['content']['parts'][0]['text']

    elif provider in ['openai', 'custom_llm']:
        url = business_settings.ai_api_url.strip() if business_settings.ai_api_url else "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temp
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['choices'][0]['message']['content']

    else:
        raise ValueError(f"Unsupported AI provider: '{provider}'")

def test_llm_connection(business_settings):
    """
    Tests LLM connection credentials.
    Returns structured result dict.
    """
    if not business_settings or not business_settings.ai_api_key:
        return {
            'success': False,
            'message': 'API Key is missing. Please enter your API Key and save settings.',
            'provider': getattr(business_settings, 'ai_provider', 'Unknown')
        }

    system_prompt = "You are a helpful AI assistant. Always respond concisely."
    test_prompt = "Say 'AI Connection Successful!' in one short sentence."

    try:
        reply = call_llm_api(business_settings, system_prompt, test_prompt)
        return {
            'success': True,
            'message': f"Connection successful! Response from {business_settings.get_ai_provider_display()}: '{reply.strip()}'",
            'provider': business_settings.get_ai_provider_display(),
            'model': business_settings.ai_model_name
        }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8') if e.fp else str(e)
        return {
            'success': False,
            'message': f"HTTP {e.code} Error calling {business_settings.get_ai_provider_display()}: {err_body[:200]}",
            'provider': business_settings.get_ai_provider_display()
        }
    except Exception as e:
        return {
            'success': False,
            'message': f"Failed to connect to {business_settings.get_ai_provider_display()}: {str(e)}",
            'provider': business_settings.get_ai_provider_display()
        }

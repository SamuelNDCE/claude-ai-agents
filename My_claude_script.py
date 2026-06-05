from anthropic import Anthropic

client = Anthropic(
    api_key="PASTE_YOUR_NEW_KEY_HERE"
)

prompt = "Say: Claude API is working."

response = client.messages.create(
    model="claude-3-5-haiku-latest",
    max_tokens=200,
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

print(response.content[0].text)
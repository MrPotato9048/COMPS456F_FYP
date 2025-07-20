import aiohttp, os

api = os.getenv('LEGEXP_API_KEY')

api_endpoint = os.getenv('LEGEXP_API_ENDPOINT')
headers = {
    "Authorization": f"Bearer {api}",
}
json_payload = {
    "prompt": "law enquiry",
    "lang": "zh"
}

async def chatbot(message):
    async with aiohttp.ClientSession(headers=headers) as session:
        json_payload["prompt"] = message
        async with session.post(api_endpoint, json=json_payload) as response:
            if response.status == 200:
                retrieved_law = await response.json()
                print(retrieved_law)
                return retrieved_law
            else:
                print(f"Failed to retrieve law. Status code: {response.status}")
                return None
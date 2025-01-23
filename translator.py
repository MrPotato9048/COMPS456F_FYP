import requests, os

key = os.getenv('TRANSLATOR_KEY') # key of azure translator api
region = os.getenv('TRANSLATOR_REGION')
endpoint = "https://api.cognitive.microsofttranslator.com"

"""def detect_language(text):
    path = '/detect'
    constructed_url = endpoint + path
    params = {'api-version': '3.0'}
    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': region,
        'Content-type': 'application/json',
    }
    body = [{'text': text}]
    response = requests.post(constructed_url, params=params, headers=headers, json=body).json()
    return response[0]['language']"""

def translate(text, source_language, target_language):
    url = endpoint + '/translate'

    params = {
        'api-version': '3.0',
        'from': source_language,
        'to': target_language
    }
    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': region,
        'Content-type': 'application/json'
    }
    body = [{
        'text': text
    }]
    try:
        print("Running translator...")
        request = requests.post(url, params=params, headers=headers, json=body)
        print("Request sent...")
        response = request.json()
        print("Response received...")

        translation = response[0]['translations'][0]['text']

        return translation
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None
    
def transliterate(text, source_language):
    url = endpoint + '/transliterate'

    match source_language:
        case 'ne':
            toScript = 'Deva'
        case 'ur':
            toScript = 'Arab'

    params = {
        'api-version': '3.0',
        'language': source_language,
        'fromScript': 'Latn',
        'toScript': toScript
    }
    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': region,
        'Content-type': 'application/json'
    }
    body = [{
        'text': text
    }]

    try:
        print("Running transliterator...")
        request = requests.post(url, params=params, headers=headers, json=body)
        print("Request sent...")
        response = request.json()
        
        print("Response received...")

        transliterated = response[0]["text"]
        
        return transliterated
    
    except  requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


        
    

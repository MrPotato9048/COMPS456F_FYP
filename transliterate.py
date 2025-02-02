import aiohttp

async def transliterate(text, source_lang): # gain uri from Google Input Tools, may not work if patched
    match source_lang:
        case 'ne':
            itc = 'ne-t-i0-und'
        case 'ur':
            itc = 'ur-t-i0-und'
        case _:
            raise ValueError("Unsupported language")

    async with aiohttp.ClientSession() as session:
        async with session.post(f'https://inputtools.google.com/request?text={text}&itc={itc}&num=5&cp=0&cs=1&ie=utf-8&oe=utf-8&app=test') as response:
            result = await response.json()
            return result[1][0][1]
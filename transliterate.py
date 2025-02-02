from ai4bharat.transliteration import XlitEngine

def engineInit(romanize):
    if romanize:
        return XlitEngine(["ne", "ur"], beam_width=10, src_script_type="indic")
    return XlitEngine(["ne", "ur"], beam_width=10) # Initialize engine with loading Nepali and Urdu dictionaries into RAM

def transliterate(engine, text, source_lang):
    return engine.translit_word(text, lang_code=source_lang, topk=5)

def romanize(engine, text, source_lang): # not sure if needed
    return engine.translit_sentence(text, lang_code=source_lang)
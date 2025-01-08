from datetime import datetime
from flask import Flask, jsonify, render_template, request, session, redirect, url_for
from flask_pymongo import PyMongo
from google.transliteration import transliterate_text
import string, os, mimetypes
import stt, tts, chatbot as c, translator as t

app = Flask(__name__)
app.debug = True # set to debug mode
db_username = os.getenv('DB_USERNAME')
db_password = os.getenv('DB_PASSWORD')
mongo = PyMongo(app, uri = f"mongodb+srv://{db_username}:{db_password}@cluster0.ctuol90.mongodb.net/FYP")
app.config['SECRET_KEY'] = 'testing_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads' # Folder to save uploaded files
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

translator_languages = ["en", "ne", "ur", "fil"] 
speech_languages = ["en-US", "ne-NP", "ur-IN", "fil-PH"]
engine_lang = "zh-Hant"

def saveDB(inputType, lang, inputText, translatedInput, outputText, translatedOutput):
    # Save data to MongoDB, not sure if to save tts audio as well
    data = {
        "datetime": datetime.now(),
        "inputType": inputType,
        "inputLang": lang,
        "inputText": inputText,
        "translatedInput": translatedInput,
        "outputText": outputText,
        "translatedOutput": translatedOutput
    }
    mongo.db.query.insert_one(data)

async def text(lang, user_input):
    print("Lang: {lang}, Engine_lang: {engine_lang}".format(lang=lang, engine_lang=engine_lang))
    translated_input = t.translate(user_input, lang, engine_lang)
    print(f"Question translated to Chinese: {translated_input}")
    chatbot_response = await c.chatbot(translated_input)

    translated_retrieved = []
    for item in chatbot_response['retrieved']:
        translated_law_text = t.translate(item['law_text'], engine_lang, lang)
        translated_law_chapter = t.translate(item['law_chapter'],  engine_lang, lang)
        translated_retrieved.append({
            'law_text': translated_law_text,
            'law_id': item['law_id'],
            'law_chapter': translated_law_chapter
        })
    translated_response = t.translate(chatbot_response['response'],  engine_lang, lang)
    saveDB("Text", lang, user_input, translated_input, {'response': chatbot_response['response'], 'retrieved': chatbot_response['retrieved']}, {'response': translated_response, 'retrieved': translated_retrieved})
    return {
        'response': translated_response,
        'retrieved': translated_retrieved
    }

async def speech(lang):
    print("Lang: {lang}, Engine_lang: {engine_lang}".format(lang=lang, engine_lang=engine_lang))
    match lang:
        case 'en':
            speech_lang = "en-US"
        case 'ne':
            speech_lang = "ne-NP"
        case 'ur':
            speech_lang = "ur-IN"
        case 'fil':
            speech_lang = "fil-PH"
    user_speech_input = stt.recognize_from_microphone(speech_lang)
    translated_input = t.translate(user_speech_input, lang, engine_lang)
    print(f"Question translated to Chinese: {translated_input}")
    chatbot_response = await c.chatbot(translated_input)

    translated_retrieved = []
    for item in chatbot_response['retrieved']:
        translated_law_text = t.translate(item['law_text'], engine_lang, lang)
        translated_law_chapter = t.translate(item['law_chapter'],  engine_lang, lang)
        translated_retrieved.append({
            'law_text': translated_law_text,
            'law_id': item['law_id'],
            'law_chapter': translated_law_chapter
        })
    translated_response = t.translate(chatbot_response['response'],  engine_lang, lang)
    saveDB("Speech", lang, user_speech_input, translated_input, {'response': chatbot_response['response'], 'retrieved': chatbot_response['retrieved']}, {'response': translated_response, 'retrieved': translated_retrieved})
    return {
        'userInput': user_speech_input,
        'response': translated_response,
        'retrieved': translated_retrieved
    }

# Allow audio uploading, used for testing only (not gonna merge with speech function)
async def audio(file_path, lang):
    print("Lang: {lang}, Engine_lang: {engine_lang}".format(lang=lang, engine_lang=engine_lang))
    match lang:
        case 'en':
            speech_lang = "en-US"
        case 'ne':
            speech_lang = "ne-NP"
        case 'ur':
            speech_lang = "ur-IN"
        case 'fil':
            speech_lang = "fil-PH"
    audio_input = stt.recognize_from_audio(file_path, speech_lang)
    translated_input = t.translate(audio_input, lang, engine_lang)
    print(f"Question translated to Chinese: {translated_input}")
    chatbot_response = await c.chatbot(translated_input)

    translated_retrieved = []
    for item in chatbot_response['retrieved']:
        translated_law_text = t.translate(item['law_text'], engine_lang, lang)
        translated_law_chapter = t.translate(item['law_chapter'],  engine_lang, lang)
        translated_retrieved.append({
            'law_text': translated_law_text,
            'law_id': item['law_id'],
            'law_chapter': translated_law_chapter
        })
    translated_response = t.translate(chatbot_response['response'],  engine_lang, lang)
    saveDB("Audio", lang, audio_input, translated_input, {'response': chatbot_response['response'], 'retrieved': chatbot_response['retrieved']}, {'response': translated_response, 'retrieved': translated_retrieved})
    return {
        'userInput': audio_input,
        'response': translated_response,
        'retrieved': translated_retrieved
    }
                                            
def is_supported_audio(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type in ['audio/wav'] # Microsoft Azure only supports .wav files
    
@app.before_request
def set_language():
    if 'lang' not in session:
        session['lang'] = "en"  # default language
    session['login'] = False # default login status, for accessing database

# can't stop TTS audio from playing when switching before webpages
"""@app.before_request
def stop_tts():
    if request.path != '/tts':
        tts.stop()"""

# language change
@app.route('/lang/<lang>')
def set_language(lang):
    session['lang'] = lang
    return redirect(url_for('chat'))

@app.route('/')
def index():
    return redirect(url_for('chat'))

@app.route('/chat', methods=['GET', 'POST'])
async def chat():
    if request.method == 'POST':
        input_type = request.json['inputType']
        user_input = request.json.get('userInput', '')
        lang = session.get('lang')
        
        if input_type == 'text':
            if lang in ['ne', 'ur']:
                user_input_cleaned = user_input.translate(str.maketrans('', '', string.punctuation)).replace(" ", "") # clean all punctuation and spaces for alphabet check
                if user_input_cleaned.strip().isalpha():
                    """user_input = t.transliterate(user_input, lang)""" # azure transliteration
                    user_input = transliterate_text(user_input, lang_code=lang) # google transliteration (deprecated)
                    print(user_input)
            response = await text(lang, user_input)
            return jsonify({
                'response': response['response'],
                'retrieved': response['retrieved']
            })
        elif input_type == 'speech':
            speech_output = await speech(lang)
            user_input = speech_output['userInput']
            response = speech_output['response']
            retrieved = speech_output['retrieved']
            print(f"userInput:  {user_input},  response: {response},   retrieved: {retrieved}")
            return jsonify({
                'user_input': user_input,
                'response': response,
                'retrieved': retrieved
            }) 
        
    lang = session.get('lang')
    return render_template('chat.html', lang=lang)

# For uploading audio
@app.route('/upload', methods=['POST'])
async def upload_audio():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)
    
    lang = session.get('lang')
    response = await audio(filepath, lang)
    return jsonify(
        {'user_input': response['userInput'],
         'response': response['response'],
         'retrieved': response['retrieved']}
    )

@app.route('/tts', methods=['POST'])
def text2speech():
    data = request.get_json()
    text = data['text']
    lang = data['lang']
    tts.speak_text(text, lang)
    return jsonify({'message': 'TTS completed'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = request.args.get('error')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == os.getenv('ADMIN_USERNAME') and password == os.getenv('ADMIN_PASSWORD'):
            session['login'] = True
            return redirect(url_for('dev'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html', error=error)

@app.route('/dev', methods=['GET'])
def dev():
    if not session.get('login'):
        return redirect(url_for('login', error='Login to access'))
    queries = mongo.db.query.find()
    processed_queries = []
    for query in queries:
        query['_id'] = str(query['_id'])
        query['datetime'] = query['datetime'].isoformat() if isinstance(query['datetime'], datetime) else query['datetime']
        processed_queries.append(query)
    return render_template('dev.html', queries=processed_queries)

if __name__ == "__main__":
    app.run()
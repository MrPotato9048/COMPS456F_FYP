from bson.objectid import ObjectId
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template, request, session, redirect, url_for
from flask_pymongo import PyMongo
import string, os, mimetypes, asyncio
import stt, tts, chatbot as c, translator as t, transliterate as tr

"""from dotenv import load_dotenv
load_dotenv()"""

app = Flask(__name__)
app.debug = True # set to debug mode
db_username = os.getenv('DB_USERNAME')
db_password = os.getenv('DB_PASSWORD')
mongo = PyMongo(app, uri = f"mongodb+srv://{db_username}:{db_password}@cluster0.ctuol90.mongodb.net/FYP")
app.config['SECRET_KEY'] = 'testing_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
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
    result = mongo.db.query.insert_one(data)
    return str(result.inserted_id)

async def text(lang, input_type, user_input):
    print("Lang: {lang}, Engine_lang: {engine_lang}".format(lang=lang, engine_lang=engine_lang))
    translated_input = await asyncio.to_thread(t.translate, user_input, lang, engine_lang)
    print(f"Question translated to Chinese: {translated_input}")
    chatbot_response = await c.chatbot(translated_input)

    async def translate_item(item):
        translated_law_text = await asyncio.to_thread(t.translate, item['law_text'], engine_lang, lang)
        translated_law_chapter = await asyncio.to_thread(t.translate, item['law_chapter'], engine_lang, lang)
        return {
            'law_text': translated_law_text,
            'law_id': item['law_id'],
            'law_chapter': translated_law_chapter
        }

    translated_retrieved = await asyncio.gather(*[translate_item(item) for item in chatbot_response['retrieved']])
    translated_response = await asyncio.to_thread(t.translate, chatbot_response['response'], engine_lang, lang)
    documentId = saveDB(input_type, lang, user_input, translated_input, {'response': chatbot_response['response'], 'retrieved': chatbot_response['retrieved']}, {'response': translated_response, 'retrieved': translated_retrieved})
    return {
        'response': translated_response,
        'retrieved': translated_retrieved,
        'documentId': documentId
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
    audio_input = await asyncio.to_thread(stt.recognize_from_audio, file_path, speech_lang)
    translated_input = await asyncio.to_thread(t.translate, audio_input, lang, engine_lang)
    print(f"Question translated to Chinese: {translated_input}")
    chatbot_response = await c.chatbot(translated_input)

    async def translate_item(item):
        translated_law_text = await asyncio.to_thread(t.translate, item['law_text'], engine_lang, lang)
        translated_law_chapter = await asyncio.to_thread(t.translate, item['law_chapter'], engine_lang, lang)
        return {
            'law_text': translated_law_text,
            'law_id': item['law_id'],
            'law_chapter': translated_law_chapter
        }

    translated_retrieved = await asyncio.gather(*[translate_item(item) for item in chatbot_response['retrieved']])
    translated_response = await asyncio.to_thread(t.translate, chatbot_response['response'], engine_lang, lang)
    documentId = saveDB("Audio", lang, audio_input, translated_input, {'response': chatbot_response['response'], 'retrieved': chatbot_response['retrieved']}, {'response': translated_response, 'retrieved': translated_retrieved})
    return {
        'userInput': audio_input,
        'response': translated_response,
        'retrieved': translated_retrieved,
        'documentId': documentId
    }
                                            
def is_supported_audio(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type in ['audio/wav'] # Microsoft Azure only supports .wav files
    
@app.before_request
def initialize():
    session.permanent = True
    if 'lang' not in session:
        session['lang'] = "en"  # default language
    if 'login' not in session:
        session['login'] = False # default login status, for accessing database

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
        if request.json.get('inputType') == 'text':
            input_type = 'Text'
        elif request.json.get('inputType') == 'speech':
            input_type = 'Speech'
        else:
            return jsonify({'error': 'Invalid input type'}), 400
        user_input = request.json.get('userInput', '')
        lang = session.get('lang')
        
        if lang in ['ne', 'ur']:
            user_input_cleaned = user_input.translate(str.maketrans('', '', string.punctuation)).replace(" ", "") # clean all punctuation and spaces for alphabet check
            if user_input_cleaned.strip().isalpha():
                print(user_input)
        response = await text(lang, input_type, user_input)
        return jsonify({
            'response': response['response'],
            'retrieved': response['retrieved'],
            'documentId': response['documentId']
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
         'retrieved': response['retrieved'],
         'documentId': response['documentId']}
    )

@app.route('/tts', methods=['POST'])
def text2speech():
    data = request.get_json()
    text = data['text']
    lang = data['lang']
    audio_filename = tts.speak_text(text, lang)
    if audio_filename:
        audio_url = url_for('static', filename=os.path.relpath(audio_filename, 'static').replace('\\', '/'))
        return jsonify({'message': 'TTS completed', 'audio_url': audio_url})
    else:
        return jsonify({'message': 'TTS failed'}), 500

@app.route('/getLaws', methods=['GET'])
def get_laws():
    document_id = request.args.get('documentId')
    query = mongo.db.query.find_one({'_id': ObjectId(document_id)})
    retrieved = query.get('translatedOutput', {}).get('retrieved', [])
    return jsonify({"laws": retrieved})


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

@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('chat'))

@app.route('/dev', methods=['GET'])
def dev():
    if not session.get('login'):
        return redirect(url_for('login', error='Login to access'))
    
    queries = mongo.db.query.find()
    processed_queries = []
    for query in queries:
        query['_id'] = str(query['_id'])
        if isinstance(query['datetime'], datetime):
            query['datetime'] = query['datetime'].strftime('%Y-%m-%d %H:%M:%S')
        processed_queries.append(query)
    
    languages = ["en", "ne", "ur", "fil"]
    
    ratings = mongo.db.rating.find()
    rateTime = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    rateAccuracy = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    suggestions = mongo.db.rating.find({'suggestions': {'$ne': ''}})
    for rating in ratings:
        rateTime[str(rating['responseTime'])] += 1
        rateAccuracy[str(rating['accuracy'])] += 1
    
    return render_template('dev.html', queries=processed_queries, languages=languages, rateTime=rateTime, rateAccuracy=rateAccuracy, suggestions=suggestions)

@app.route('/delete', methods=['DELETE'])
def delete():
    query_ids = request.json.get('queryIds')
    if not session.get('login'):
        return redirect(url_for('login', error='Login to access'))
    try:
        object_ids = [ObjectId(query_id) for query_id in query_ids]
        result = mongo.db.query.delete_many({'_id': {'$in': object_ids}})
        if result.deleted_count > 0:
            if result.deleted_count == 1:
                return jsonify({'message': f'{result.deleted_count} query deleted successfully'}), 200
            else:
                return jsonify({'message': f'{result.deleted_count} queries deleted successfully'}), 200
        else:
            return jsonify({'error': 'No queries found or already deleted'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/transliterate', methods=['GET'])
async def transliterate():
    text = request.args.get('text')
    lang = request.args.get('lang')

    suggestions = await tr.transliterate(text, lang)
    print(f"Transliterate suggestions: {suggestions}")
    return jsonify(suggestions=suggestions)

@app.route('/update_duration', methods=['POST'])
def update_duration():
    documentId = request.json['documentId']
    print(f"Updating duration for document {documentId}")
    duration = round(request.json['duration'], 2)
    mongo.db.query.update_one({'_id': ObjectId(documentId)}, {'$set': {'duration': duration}})
    return jsonify({'message': 'Duration updated successfully'}), 200

@app.route('/rate', methods=['POST'])
def rate():
    responseTime = request.json['responseTime']
    accuracy = request.json['accuracy']
    suggestions = request.json['suggestions']
    mongo.db.rating.insert_one({'responseTime': responseTime, 'accuracy': accuracy, 'suggestions': suggestions})
    return jsonify({'message': 'Rating submitted successfully'}), 200

if __name__ == "__main__":
    app.run()
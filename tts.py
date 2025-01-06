import azure.cognitiveservices.speech as speechsdk
from config import config

configuration = config()
key, region = configuration['SPEECH_KEY'], configuration['SPEECH_REGION']
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
speech_config = speechsdk.SpeechConfig(subscription=key, region=region)

# somehow can stop audio playing

"""isSpeaking = False

def synthesis_started(event):
    global isSpeaking
    isSpeaking = True

def synthesis_completed(event):
    global isSpeaking
    isSpeaking = False

speech_synthesizer.synthesis_started.connect(synthesis_started)
speech_synthesizer.synthesis_completed.connect(synthesis_completed)"""

def speak_text(text, lang):
    # global isSpeaking
    match lang:
        case "en":
            speech_config.speech_synthesis_voice_name='en-US-AvaMultilingualNeural'
        case "ne":
            speech_config.speech_synthesis_voice_name='ne-NP-HemkalaNeural'
        case "ur":
            speech_config.speech_synthesis_voice_name='ur-PK-UzmaNeural'
        case "fil":
            speech_config.speech_synthesis_voice_name='fil-PH-BlessicaNeural'

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

    """# save the speech audio to computer as wav file
    stream = speechsdk.AudioDataStream(speech_synthesis_result)
    stream.save_to_wav_file("/output/tts.wav)"""

    print("Running TTS...")

    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized for text [{}]".format(text))
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")

"""def stop():
    global isSpeaking
    if isSpeaking:
        print("Stopping TTS...")
        speech_synthesizer.stop_speaking_async()
        print("TTS stopped successfully")
        isSpeaking = False"""
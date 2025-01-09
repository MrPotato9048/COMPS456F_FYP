import azure.cognitiveservices.speech as speechsdk
import os, uuid

key, region = os.getenv('SPEECH_KEY'), os.getenv('SPEECH_REGION')
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
speech_config = speechsdk.SpeechConfig(subscription=key, region=region)

def speak_text(text, lang):
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

    print("Running TTS...")

    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized for text [{}]".format(text))
        output_dir = os.path.join(os.getcwd(), 'static', 'output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        audio_filename = os.path.join(output_dir, f"{uuid.uuid4()}.wav")
        stream = speechsdk.AudioDataStream(speech_synthesis_result)
        stream.save_to_wav_file(audio_filename)
        return audio_filename
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")
        return None
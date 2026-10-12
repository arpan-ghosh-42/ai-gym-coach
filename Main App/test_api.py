import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GROQ_API_KEY')
print('GROQ_API_KEY loaded:', bool(api_key))

if not api_key:
    print('Missing GROQ_API_KEY, aborting')
else:
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        print('Groq client created')
        from services.coaching.llm import LLMCoach
        coach = LLMCoach(client)
        try:
            feedback = coach.give_feedback('Test event', '')
            print('Feedback sample:', feedback[:100])
        except Exception as e:
            print('Error during LLM feedback:', e)
    except Exception as e:
        print('Error importing/using Groq:', e)

try:
    from services.coaching.tts import TextToSpeech
    tts = TextToSpeech()
    audio = tts.speak('Hello world')
    if audio:
        print('TTS audio bytes length:', len(audio))
    else:
        print('TTS returned no audio')
except Exception as e:
    print('Error with TTS:', e)


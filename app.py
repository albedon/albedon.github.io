from flask import Flask, render_template, request
import speech_recognition as sr
import textwrap
import pyttsx3
import threading
import google.generativeai as genai
from IPython.display import Markdown
import atexit
import time

app = Flask(__name__)

class SpeakerSystem:
    def __init__(self):
        self.stop_listening = False
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # Adjust speech rate if needed

    def stop_listening_after_timeout(self, timeout):
        time.sleep(timeout)
        self.stop_listening = True

    def speech_to_text(self, max_timeout=20):
        recognizer = sr.Recognizer()

        with sr.Microphone() as source:
            print("Listening for a prompt...")
            recognizer.adjust_for_ambient_noise(source)

            timeout_thread = threading.Thread(target=self.stop_listening_after_timeout, args=(max_timeout,))
            timeout_thread.start()

            try:
                audio = recognizer.listen(source, timeout=max_timeout, phrase_time_limit=5)
                text = recognizer.recognize_google(audio)
                print(f"User said: {text}")
                return text
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
            finally:
                self.stop_listening = True

        print("Speech recognition timeout reached.")
        return None

    def text_to_speech(self, text, speed=1.5):
        with self.speech_lock:
            # Replace asterisks with an empty string
            cleaned_text = str(text.data).replace('*', '')
            
            self.engine.setProperty('rate', speed * 100)  # Adjust speed for pyttsx3
            self.engine.say(cleaned_text)
            self.engine.runAndWait()

# Configure API key
genai.configure(api_key="[KEY]")

# Choose model
model = genai.GenerativeModel('gemini-pro')
chat = model.start_chat(history=[])

# Set up SpeakerSystem instance
speaker = SpeakerSystem()

@atexit.register
def cleanup():
    speaker.engine.stop()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_input', methods=['POST'])
def process_input():
    user_input = request.form['user_input']
    response = chat.send_message(user_input)

    if response:
        text = textwrap.indent(str(response.text).replace('•', '  *'), ' ', predicate=lambda _: True)
        markdown_text = Markdown(text)
        speaker.text_to_speech(markdown_text)
        print(f"Gemini said: {text}")

    return render_template('index.html', response=text)

@app.route('/speech_input')
def speech_input():
    user_input = speaker.speech_to_text()
    return render_template('index.html', user_input=user_input)

if __name__ == '__main__':
    app.run(debug=True)

import speech_recognition as sr
import asyncio
import edge_tts
import subprocess
import uuid
import os
import requests

recognizer = sr.Recognizer()

# --- Ollama LLM ---
def ask_ollama(prompt):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            }
        )
        return response.json().get("response", "I couldn't generate a response.")
    except Exception as e:
        return f"Ollama error: {str(e)}"

# --- TTS ---
async def speak_async(text):
    filename = f"{uuid.uuid4()}.mp3"
    communicate = edge_tts.Communicate(text, voice="en-US-JennyNeural")
    await communicate.save(filename)
    subprocess.run(
        ["ffplay", "-nodisp", "-autoexit", filename],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    os.remove(filename)

def speak(text):
    print("Assistant:", text)
    asyncio.run(speak_async(text))

# --- STT ---
def listen():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            speak("I didn't hear anything.")
            return ""
        try:
            text = recognizer.recognize_google(audio)
            print("You:", text)
            return text.lower()
        except:
            speak("Sorry, I didn't catch that.")
            return ""

# --- Command Handler ---
def handle_command(text):
    if "stop" in text or "exit" in text or "quit" in text:
        speak("Goodbye Madhuri!")
        return False

    # Everything else goes to Ollama
    print("Thinking...")
    reply = ask_ollama(text)
    speak(reply)
    return True

# --- Main ---
def main():
    speak("Hi Madhuri, I am ready. Say something!")
    running = True
    while running:
        text = listen()
        if text:
            running = handle_command(text)

main()
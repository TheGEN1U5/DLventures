from flask import Flask, g, render_template, request, redirect, url_for, session, jsonify
import base64

app = Flask(__name__)
app.secret_key = 'super-secret-key'  # For session storage
from gemini_chat import *

chat_store = {}

# Route 1: Entry form for name + emotion
@app.route('/')
def index():
    return render_template('index.html')

@app.before_request
def load_chat():
    chat_id = session.get("chat_id")
    if chat_id and chat_id in chat_store:
        g.chat = chat_store[chat_id]
    else:
        g.chat = None

# Route 2: Start the chat session
@app.route('/start-chat', methods=['POST'])
def start_chat():
    session['username'] = request.form['username']
    session['target_emotion'] = request.form['emotion']
    chat = init_chat()
    chat_id = str(id(chat))
    chat_store[chat_id] = chat
    session['chat_id'] = chat_id
    return redirect(url_for('chat'))

# Route 3: Chat page
@app.route('/chat')
def chat():
    return render_template('chat.html', username=session.get('username'))

# Route 4: Handle chat messages
@app.route('/send', methods=['POST'])
def send():
    user_msg = request.form['message']
    if g.chat is None:
        return "No chat found", 400
    bot_msg = get_reply(g.chat, user_msg)
    # tts_b64  = get_audio(bot_msg)
    tts_b64=None
    return {"response": bot_msg, "audio_base64": tts_b64}


@app.route("/send-voice", methods=["POST"])
def send_voice():
    data = request.get_json()
    audio_b64 = data["audio"]
    audio_bytes = base64.b64decode(audio_b64)
    bot_msg = send_voice_to_chat(g.chat, audio_bytes)
    # tts_b64  = get_audio(bot_msg)
    tts_b64=None

    return jsonify({
        "response": bot_msg,
        "audio_base64": tts_b64
    })

def get_score_color(score):
    score = float(score)
    if score >= 90:
        return "score-green"
    elif score >= 60:
        return "score-yellow"
    elif score >= 30:
        return "score-orange"
    else:
        return "score-red"

# Route 5: End chat and evaluate emotion
@app.route('/result')
def result():
    target = session.get('target_emotion', 'unknown')
    if g.chat is None:
        return "No chat found", 400
    result = get_result(g.chat, target)
    return render_template('result.html', target=target, actual=result["emotion_felt"], reason=result["reasoning"], score=result["score"], get_score_color=get_score_color)

if __name__ == '__main__':
    app.run(debug=True)

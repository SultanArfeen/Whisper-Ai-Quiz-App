import os
import random
import re
from difflib import SequenceMatcher

import gradio as gr
import whisper
from gtts import gTTS
from pydub import AudioSegment

# Load the Whisper model (using the "base" model)
model = whisper.load_model("base")

def similar(a, b):
    """Return a similarity ratio between two strings."""
    return SequenceMatcher(None, a, b).ratio()

def generate_deep_tts(text, filename, lang="en", semitones=-4, speed_factor=1.5):
    """
    Generate TTS audio using gTTS, then apply a pitch shift and speedup
    to produce a deep male voice.
    """
    temp_filename = "temp_" + filename
    tts = gTTS(text=text, lang=lang)
    tts.save(temp_filename)
    
    # Process the audio: pitch shift and speed up.
    audio = AudioSegment.from_file(temp_filename)
    new_sample_rate = int(audio.frame_rate * (2.0 ** (semitones / 12.0)))
    shifted = audio._spawn(audio.raw_data, overrides={'frame_rate': new_sample_rate})
    deep_audio = shifted.set_frame_rate(audio.frame_rate)
    sped_audio = deep_audio.speedup(playback_speed=speed_factor, chunk_size=150, crossfade=25)
    sped_audio.export(filename, format="mp3")
    os.remove(temp_filename)
    return filename

# -------------------------------
# Main Questions (10 total)
# -------------------------------
main_questions = [
    {
        "question": "What is the primary function of a convolutional neural network (CNN)?",
        "options": [
            "Option A: Image classification",
            "Option B: Natural language processing",
            "Option C: Data encryption",
            "Option D: Video streaming"
        ],
        "correct": "a"
    },
    {
        "question": "Which optimization algorithm is commonly used in deep learning?",
        "options": [
            "Option A: Dijkstra's algorithm",
            "Option B: Gradient descent",
            "Option C: Merge sort",
            "Option D: Binary search"
        ],
        "correct": "b"
    },
    {
        "question": "Which principle in physics describes wave–particle duality?",
        "options": [
            "Option A: Heisenberg's Uncertainty Principle",
            "Option B: Superposition Principle",
            "Option C: Complementarity Principle",
            "Option D: Newton's Laws"
        ],
        "correct": "c"
    },
    {
        "question": "Which field primarily deals with the design and analysis of algorithms?",
        "options": [
            "Option A: Artificial Intelligence",
            "Option B: Theoretical Computer Science",
            "Option C: Organic Chemistry",
            "Option D: Sociology"
        ],
        "correct": "b"
    },
    {
        "question": "What does 'GPU' stand for in computer hardware?",
        "options": [
            "Option A: General Processing Unit",
            "Option B: Graphical Processing Unit",
            "Option C: Geometric Programming Unit",
            "Option D: Global Processing Unit"
        ],
        "correct": "b"
    },
    {
        "question": "Which city is recognized as a major tech hub in Pakistan?",
        "options": [
            "Option A: Lahore",
            "Option B: Karachi",
            "Option C: Islamabad",
            "Option D: Peshawar"
        ],
        "correct": "c"
    },
    {
        "question": "What is the main purpose of a generative model?",
        "options": [
            "Option A: Data classification",
            "Option B: Clustering data",
            "Option C: Generating new data similar to training data",
            "Option D: Data storage"
        ],
        "correct": "c"
    },
    {
        "question": "Which protocol is used for secure communication over the Internet?",
        "options": [
            "Option A: HTTP",
            "Option B: FTP",
            "Option C: HTTPS",
            "Option D: SMTP"
        ],
        "correct": "c"
    },
    {
        "question": "Which programming language is most popular for AI research?",
        "options": [
            "Option A: C++",
            "Option B: Java",
            "Option C: Python",
            "Option D: Ruby"
        ],
        "correct": "c"
    },
    {
        "question": "What is the primary purpose of machine learning?",
        "options": [
            "Option A: Website development",
            "Option B: Analyzing and learning from data",
            "Option C: Managing databases",
            "Option D: Designing hardware"
        ],
        "correct": "b"
    }
]

# -------------------------------
# Secret Question (Roman Urdu)
# -------------------------------
secret_question = {
    "question": "Agar alu ka paratha tumne kha liya to alu kya khaye ga?",
    "options": [
        "Option A: Alu kaila khaye ga",
        "Option B: Alu mar jayega",
        "Option C: Alu ki maa moti",
        "Option D: Alu tumhe khaye ga"
    ],
    "correct": "b"
}

def build_combined_text(question, options, prompt):
    """Combine question, options, and prompt into one string."""
    combined = question + " "
    for opt in options:
        combined += opt + ". "
    combined += prompt
    return combined

def start_main_question(existing_state):
    """Randomly select a main question and prepare its display and TTS audio."""
    qdata = random.choice(main_questions)
    combined_text = build_combined_text(qdata["question"], qdata["options"], "Which option do you choose?")
    audio_file = generate_deep_tts(combined_text, "main_question.mp3", lang="en", semitones=-4, speed_factor=1.5)
    instructions = "Listen to the question and options, then record your answer (say 'Option A' or just 'A')."
    options_text = "\n".join(qdata["options"])
    if existing_state is None:
        new_state = {"type": "main", "question": qdata, "score": 0, "total": 0}
    else:
        new_state = existing_state
        new_state["type"] = "main"
        new_state["question"] = qdata
    return qdata["question"], options_text, audio_file, instructions, new_state

def start_secret_question(existing_state):
    """Prepare the secret question (in Roman Urdu) for display and TTS audio."""
    qdata = secret_question
    combined_text = build_combined_text(qdata["question"], qdata["options"], "Which option do you choose?")
    audio_file = generate_deep_tts(combined_text, "secret_question.mp3", lang="hi", semitones=-4, speed_factor=1.5)
    instructions = "Listen to the secret question and options, then record your answer (say 'Option B' or just 'B')."
    options_text = "\n".join(qdata["options"])
    if existing_state is None:
        new_state = {"type": "secret", "question": qdata, "score": 0, "total": 0}
    else:
        new_state = existing_state
        new_state["type"] = "secret"
        new_state["question"] = qdata
    return qdata["question"], options_text, audio_file, instructions, new_state

def process_answer(user_audio, state):
    """
    Transcribe the user's answer, update progress, and return result feedback.
    
    For main questions:
      - If correct: "Your answer is correct. You have won 10 rupees."
      - If incorrect: "Incorrect. The correct option was: [Correct Option]. You now owe us 10 rupees."
      (Deduct 10 rupees by subtracting 1 point from score.)
      
    For the secret question:
      - If correct: "Aap ka jawab sahi hai. Aap jeet gaye hain, 100 rupees."
      - If incorrect: "Galat Jawab. Sahee Jawab Ye Hai Ke [Correct Option]. You now owe us 10 rupees."
      (Deduct 10 rupees by subtracting 1 point.)
    
    Progress is updated as Money Earned: (score * 10) Rupees (Fake).
    """
    if user_audio is None:
        progress = f"Money Earned: {state['score'] * 10} Rupees (Fake)"
        return None, "No audio detected. Please record your answer.", progress, state
    
    result = model.transcribe(user_audio)
    transcribed = result["text"].strip().lower()
    match = re.search(r'\b(?:option\s*)?([a-d])\b', transcribed, re.IGNORECASE)
    answer_letter = match.group(1).lower() if match else ""
    
    # Map letters to index for option text
    option_index = {"a": 0, "b": 1, "c": 2, "d": 3}
    
    if state["type"] == "main":
        correct = state["question"]["correct"]
        correct_option_text = state["question"]["options"][option_index[correct]]
        if answer_letter == correct:
            result_text = "Your answer is correct. You have won 10 rupees."
            state["score"] += 1
        else:
            result_text = f"Incorrect. The correct option was: {correct_option_text}. You now owe us 10 rupees."
            state["score"] -= 1
        result_audio = generate_deep_tts(result_text, "result.mp3", lang="en", semitones=-4, speed_factor=1.5)
    else:  # secret question
        correct = state["question"]["correct"]
        correct_option_text = state["question"]["options"][option_index[correct]]
        if answer_letter == correct:
            result_text = "Aap ka jawab sahi hai. Aap jeet gaye hain, 100 rupees."
            state["score"] += 10
        else:
            result_text = f"Galat Jawab. Sahee Jawab Ye Hai Ke {correct_option_text}. You now owe us 10 rupees."
            state["score"] -= 1
        result_audio = generate_deep_tts(result_text, "result.mp3", lang="hi", semitones=-4, speed_factor=1.5)
    
    state["total"] += 1
    progress = f"Money Earned: {state['score'] * 10} Rupees (Fake)"
    
    return result_audio, result_text, progress, state

# -------------------------------
# Build the Gradio Interface
# -------------------------------
with gr.Blocks(css="""
    body { background-color: #007BFF; color: white; }
    .title { font-family: 'Times New Roman', serif; font-size: 36px; color: white; text-align: center; }
    .gr-button { font-size: 16px; margin: 5px; }
    .gr-input { font-size: 16px; }
    .bottom-buttons { margin-top: 20px; }
    .progress { font-size: 18px; text-align: center; margin-bottom: 10px; }
""") as demo:
    gr.Markdown("<div class='title'>KON BNEGA KRORPATI</div>")
    
    # Progress display at the top
    progress_box = gr.Textbox(label="Progress", interactive=False, value="Money Earned: 0 Rupees (Fake)")
    
    # Top: Start Quiz button (resets progress)
    start_btn = gr.Button("Start Quiz")
    
    # Display area for question, options, question audio, and instructions
    question_box = gr.Textbox(label="Question", interactive=False)
    options_box = gr.Textbox(label="Options", interactive=False)
    audio_player = gr.Audio(label="Question Audio", type="filepath")
    instructions_box = gr.Textbox(label="Instructions", interactive=False)
    
    start_outputs = [question_box, options_box, audio_player, instructions_box]
    
    # Row for answer recording and Submit Answer button (Submit button directly below recording)
    answer_audio = gr.Audio(label="Record Your Answer", type="filepath")
    submit_btn = gr.Button("Submit Answer")
    
    # Display area for result audio and text feedback
    result_audio_player = gr.Audio(label="Result Audio", type="filepath")
    result_text_box = gr.Textbox(label="Result", interactive=False)
    
    # Bottom row: Next Question and Secret Question buttons
    with gr.Row(elem_classes="bottom-buttons"):
        next_btn = gr.Button("Next Question")
        secret_btn = gr.Button("Secret Question")
    
    # Hidden state to store current question info and progress
    state = gr.State()
    
    # Define interactions:
    # Start Quiz resets state (progress resets)
    start_btn.click(fn=lambda: start_main_question(None),
                    outputs=[question_box, options_box, audio_player, instructions_box, state])
    
    # Next Question and Secret Question use existing state to retain progress.
    next_btn.click(fn=start_main_question,
                   inputs=[state],
                   outputs=[question_box, options_box, audio_player, instructions_box, state])
    secret_btn.click(fn=start_secret_question,
                     inputs=[state],
                     outputs=[question_box, options_box, audio_player, instructions_box, state])
    
    # Submit Answer processes the answer and updates progress.
    submit_btn.click(fn=process_answer,
                     inputs=[answer_audio, state],
                     outputs=[result_audio_player, result_text_box, progress_box, state])
    
    demo.launch(share=True)

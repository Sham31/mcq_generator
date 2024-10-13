import spacy
import random
import streamlit as st
import fitz  # PyMuPDF for PDF extraction
import moviepy.editor as mp
import speech_recognition as sr
import os

# Check if the model is already downloaded
if not os.path.exists("en_core_web_sm"):
    spacy.cli.download("en_core_web_sm")

# Load SpaCy model
nlp = spacy.load('en_core_web_sm')

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text += page.get_text()
    return text

# Function to process video and extract text
def process_video(video_file):
    video_path = "uploaded_video.mp4"
    with open(video_path, "wb") as f:
        f.write(video_file.getbuffer())

    audio_file = "extracted_audio.wav"

    try:
        # Extract audio from video
        with mp.VideoFileClip(video_path) as video_clip:
            video_clip.audio.write_audiofile(audio_file, codec='pcm_s16le')

        # Convert audio to text
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)

    except sr.UnknownValueError:
        st.error("Google Speech Recognition could not understand the audio.")
        return ""
    except sr.RequestError as e:
        st.error(f"Could not request results from Google Speech Recognition service; {e}")
        return ""
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return ""
    finally:
        # Clean up files
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(audio_file):
            os.remove(audio_file)

    return text

# Function to generate MCQs
def generate_mcqs(text, num_questions=5):
    doc = nlp(text)
    sentences = [sentence.text for sentence in doc.sents]

    # Use the lesser of the requested number of questions or available sentences
    selected_questions_count = min(num_questions, len(sentences))
    selected_sentences = random.sample(sentences, selected_questions_count)

    mcqs = []
    for sentence in selected_sentences:
        sent_doc = nlp(sentence)
        nouns = [token.text for token in sent_doc if token.pos_ == "NOUN"]
        if len(nouns) < 1:
            continue

        subject = nouns[0]
        question_stem = sentence.replace(subject, "_______")
        answer_choices = [subject]

        all_tokens = [token.text for token in doc if token.pos_ in ["NOUN", "PROPN", "ADJ"] and token.text != subject]
        distractors = list(set(all_tokens) - set(answer_choices))

        while len(distractors) < 3:
            distractors.append("[Distractor]")

        random.shuffle(distractors)
        distractors = distractors[:3]

        answer_choices.extend(distractors)
        random.shuffle(answer_choices)

        correct_answer = chr(65 + answer_choices.index(subject))
        mcqs.append((question_stem, answer_choices, correct_answer))

    return mcqs

# Function to create a text file from MCQs
def create_text(mcqs):
    text_content = ""
    for idx, (question, choices, correct_answer) in enumerate(mcqs):
        text_content += f"Q{idx + 1}: {question}\n"
        for i, choice in enumerate(choices):
            text_content += f"    {chr(65 + i)}. {choice}\n"
        text_content += f"Correct Answer: {correct_answer}\n\n"
    return text_content

# Initialize Session State for tracking user actions
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}

if "check_clicked" not in st.session_state:
    st.session_state.check_clicked = False

if "mcqs" not in st.session_state:
    st.session_state.mcqs = []

if "text_source" not in st.session_state:
    st.session_state.text_source = ""

if "video_processed" not in st.session_state:
    st.session_state.video_processed = None

if "generate_clicked" not in st.session_state:
    st.session_state.generate_clicked = False

# Sidebar for navigation
st.sidebar.title("Navigation")
st.sidebar.header("📝Instructions")
st.sidebar.write("1. Upload a PDF or Video file to extract text.")
st.sidebar.write("2. Select the difficulty level and the number of questions.")
st.sidebar.write("3. Generate MCQs and check your answers.")
st.sidebar.write("4. Download the MCQs as a PDF or text file.")

# Sidebar options for settings
st.sidebar.header("Settings")
difficulty = st.sidebar.selectbox("Select difficulty level", options=["Easy", "Medium", "Hard"])
num_questions = st.sidebar.selectbox("Select number of questions", options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], index=4)

# Feedback section
st.sidebar.header("📧 Feedback")
feedback = st.sidebar.text_area("Your feedback:", placeholder="Let us know your thoughts...")
if st.sidebar.button("Submit Feedback"):
    st.sidebar.success("Thank you for your feedback!")

# Streamlit UI for PDF or Video upload
st.title("PDF/Video to MCQ Generator")
uploaded_file = st.file_uploader(
    "Upload a PDF or Video file (In case of video, please upload a smaller video; we are working on handling larger videos soon)",
    type=["pdf", "mp4"])

if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        with st.spinner("Extracting text from PDF..."):
            pdf_text = extract_text_from_pdf(uploaded_file)
            st.session_state.text_source = pdf_text
    elif uploaded_file.type == "video/mp4":
        if st.session_state.video_processed != uploaded_file.name:
            with st.spinner("Processing video..."):
                st.session_state.text_source = process_video(uploaded_file)
                st.session_state.video_processed = uploaded_file.name

# Generate MCQs Button
if st.button("Generate MCQs") and st.session_state.text_source:
    st.session_state.generate_clicked = True
    st.session_state.mcqs = generate_mcqs(st.session_state.text_source, num_questions)
    st.session_state.user_answers = {idx: None for idx in range(len(st.session_state.mcqs))}
    st.session_state.check_clicked = False  # Reset check flag

# MCQ Display
if st.session_state.generate_clicked:
    st.subheader("Generated MCQs")
    mcqs = st.session_state.mcqs

    for idx, (question, choices, correct_answer) in enumerate(mcqs):
        st.write(f"**Q{idx + 1}.** {question}")

        # Add a placeholder to the choices
        choices_with_placeholder = ["Select an answer"] + choices

        # Store the user's selected answer in session state
        st.radio(
            f"Choose an option for Q{idx + 1}:",
            choices_with_placeholder,
            index=0 if st.session_state.user_answers[idx] is None else choices_with_placeholder.index(
                st.session_state.user_answers[idx]),
            key=f"radio_{idx}",
            on_change=lambda idx=idx: st.session_state.user_answers.update({idx: st.session_state[f"radio_{idx}"]})
        )

    # Check Answers Button
    if st.button("Check Answers"):
        st.session_state.check_clicked = True

    # Show Results
    if st.session_state.check_clicked:
        st.subheader("Results")
        correct_count = 0
        for idx, (question, choices, correct_answer) in enumerate(mcqs):
            st.write(f"**Q{idx + 1}.** {question}")
            selected_answer = st.session_state.user_answers[idx]

            if selected_answer == "Select an answer" or selected_answer is None:
                st.write(f"⚠️ **No option selected for this question!**")
            else:
                correct_answer_text = \
                [choice for choice in choices if chr(65 + choices.index(choice)) == correct_answer][0]
                if selected_answer == correct_answer_text:
                    st.write("✅ **Correct!**")
                    correct_count += 1
                else:
                    st.write(f"❌ **Wrong!** The correct answer is **{correct_answer_text}**.")
            st.write("---")
        st.write(f"Your score: {correct_count}/{len(mcqs)}")

    # Download MCQs as Text
    if st.session_state.mcqs:
        st.subheader("Download MCQs")
        text_content = create_text(st.session_state.mcqs)
        st.download_button(
            label="Download as Text",
            data=text_content,
            file_name="mcqs.txt",
            mime="text/plain"
        )

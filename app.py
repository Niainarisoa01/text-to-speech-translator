import streamlit as st
from googletrans import Translator
from gtts import gTTS
import os
import tempfile
import base64
from datetime import datetime
import time
import speech_recognition as sr
from pydub import AudioSegment
import io
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
import asyncio
import re
import subprocess

# Set page config - MUST be the first Streamlit command
st.set_page_config(
    page_title="Text-to-Speech Translator",
    page_icon="🗣️",
    layout="wide"
)

# Check FFmpeg availability
def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

# Global flag for FFmpeg availability
FFMPEG_AVAILABLE = check_ffmpeg()

if not FFMPEG_AVAILABLE:
    st.warning("""
    ⚠️ FFmpeg n'est pas détecté sur votre système. Certaines fonctionnalités audio peuvent être limitées.
    Pour installer FFmpeg:
    1. Ouvrez un nouveau terminal PowerShell
    2. Exécutez: winget install -e --id Gyan.FFmpeg
    3. Redémarrez votre terminal et l'application
    """)

# Load environment variables
load_dotenv()

# Language options with codes and display names
LANGUAGES = {
    'en': 'English',
    'fr': 'French',
    'es': 'Spanish',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ja': 'Japanese',
    'zh-cn': 'Chinese (Simplified)',
    'ar': 'Arabic'
}

# Speech recognition language mapping
SR_LANGUAGES = {
    'en': 'en-US',
    'fr': 'fr-FR',
    'es': 'es-ES',
    'de': 'de-DE',
    'it': 'it-IT',
    'pt': 'pt-BR',
    'ru': 'ru-RU',
    'ja': 'ja-JP',
    'zh-cn': 'zh-CN',
    'ar': 'ar-SA'
}

# Azure TTS voice mapping (more natural voices)
AZURE_VOICES = {
    'en': 'en-US-AriaNeural',
    'fr': 'fr-FR-DeniseNeural',
    'es': 'es-ES-ElviraNeural',
    'de': 'de-DE-KatjaNeural',
    'it': 'it-IT-ElsaNeural',
    'pt': 'pt-BR-FranciscaNeural',
    'ru': 'ru-RU-SvetlanaNeural',
    'ja': 'ja-JP-NanamiNeural',
    'zh-cn': 'zh-CN-XiaoxiaoNeural',
    'ar': 'ar-SA-ZariyahNeural'
}

async def translate_text_async(text, target_lang):
    """Async function to translate text"""
    translator = Translator()
    translation = await translator.translate(text, dest=target_lang)
    return translation.text

def translate_text(text, target_lang):
    """Synchronous wrapper for the async translation function"""
    try:
        # Use a different approach to handle the coroutine
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(translate_text_async(text, target_lang))
        loop.close()
        return result
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        # Fallback to direct approach if async fails
        try:
            translator = Translator()
            translation = translator.translate(text, dest=target_lang)
            if hasattr(translation, 'text'):
                return translation.text
            return text
        except:
            return text  # Return original text if all translation attempts fail

def text_to_speech(text, lang):
    """Generate speech using gTTS (standard quality)"""
    tts = gTTS(text=text, lang=lang)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
        tts.save(fp.name)
        return fp.name

def text_to_speech_improved(text, lang):
    """Generate better quality speech by breaking text into natural phrases"""
    try:
        # Break text at punctuation for better phrasing
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        if len(sentences) <= 1:
            # If there's only one sentence, use standard TTS
            return text_to_speech(text, lang)
        
        audio_files = []
        # Create audio for each sentence with a slight pause between
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            tts = gTTS(text=sentence.strip(), lang=lang)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                tts.save(fp.name)
                audio_files.append(fp.name)
        
        if not audio_files:
            return text_to_speech(text, lang)
            
        # Check if FFmpeg is available before attempting to combine audio
        if not FFMPEG_AVAILABLE:
            st.warning("FFmpeg n'est pas disponible. Utilisation de la voix standard.")
            # Clean up temporary files
            for file in audio_files:
                try:
                    os.unlink(file)
                except:
                    pass
            return text_to_speech(text, lang)
            
        # Combine audio files with pydub
        try:
            combined = AudioSegment.empty()
            for audio_file in audio_files:
                try:
                    segment = AudioSegment.from_mp3(audio_file)
                    combined += segment
                    # Add a small pause between sentences
                    combined += AudioSegment.silent(duration=300)
                except Exception as e:
                    st.error(f"Erreur lors du traitement du fichier audio: {str(e)}")
                    # If there's an error with one file, try to continue with others
                    continue
                
            if len(combined) == 0:
                raise Exception("Aucun segment audio n'a pu être traité")
                
            # Save combined file
            output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
            combined.export(output_file, format="mp3")
            
            # Clean up temporary files
            for file in audio_files:
                try:
                    os.unlink(file)
                except:
                    pass
                    
            return output_file
        except Exception as e:
            st.warning(f"Erreur lors de la combinaison audio: {str(e)}. Utilisation de la voix standard.")
            # If audio combining fails, fall back to simple TTS
            for file in audio_files:
                try:
                    os.unlink(file)
                except:
                    pass
            return text_to_speech(text, lang)
    except Exception as e:
        st.warning(f"Erreur dans la voix améliorée: {str(e)}. Utilisation de la voix standard.")
        return text_to_speech(text, lang)

def text_to_speech_azure(text, lang):
    """Generate more human-like speech using Azure Speech Service"""
    # Check if Azure key is available
    speech_key = os.getenv('AZURE_SPEECH_KEY')
    speech_region = os.getenv('AZURE_SPEECH_REGION')
    
    if not speech_key or not speech_region:
        # Fall back to improved TTS if Azure keys aren't available
        return text_to_speech_improved(text, lang)
    
    # Create a speech config with the Azure keys
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    
    # Set the voice based on the language
    voice_name = AZURE_VOICES.get(lang, AZURE_VOICES['en'])
    speech_config.speech_synthesis_voice_name = voice_name
    
    # Create a temporary file to save the audio
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    audio_config = speechsdk.audio.AudioOutputConfig(filename=temp_file.name)
    
    # Create the synthesizer
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    
    # Synthesize speech
    result = speech_synthesizer.speak_text_async(text).get()
    
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return temp_file.name
    else:
        # Fall back to improved TTS if Azure fails
        st.warning(f"Azure Speech synthesis failed: {result.reason}. Using enhanced TTS instead.")
        return text_to_speech_improved(text, lang)

def get_download_link(audio_path, filename):
    """Generate a download link for an audio file"""
    with open(audio_path, "rb") as file:
        audio_bytes = file.read()
    b64 = base64.b64encode(audio_bytes).decode()
    href = f'<a href="data:audio/mp3;base64,{b64}" download="{filename}">Download {filename}</a>'
    return href

def speech_to_text(audio_bytes, language):
    """Convert speech to text using Google Speech Recognition"""
    # Save the uploaded audio to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_audio:
        tmp_audio.write(audio_bytes)
        tmp_audio_path = tmp_audio.name
    
    # Convert to WAV format for speech recognition
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(tmp_audio_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language=SR_LANGUAGES.get(language, language))
            os.unlink(tmp_audio_path)  # Clean up temporary file
            return text
    except Exception as e:
        os.unlink(tmp_audio_path)  # Clean up temporary file
        return f"Error recognizing audio: {str(e)}"

# Add custom CSS
st.markdown("""
    <style>
    .stApp {
        max-width: 1000px;
        margin: 0 auto;
    }
    .main {
        padding: 2rem;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 24px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 16px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .download-link {
        margin: 10px 0;
        padding: 10px;
        border-radius: 4px;
        background-color: #f1f1f1;
    }
    h1 {
        color: #2E86C1;
    }
    .info-box {
        background-color: #e7f3fe;
        border-left: 6px solid #2196F3;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for history
if 'history' not in st.session_state:
    st.session_state.history = []

# Create a settings tab for API keys
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Text Translation", "Speech to Text", "History", "Settings", "About"])

with tab4:
    st.header("Settings")
    st.markdown("### Voice Settings")
    
    voice_quality = st.radio(
        "Choose voice quality:",
        ["Standard (Google TTS)", "Premium (Human-like Azure TTS)"],
        index=1
    )
    
    if voice_quality == "Premium (Human-like Azure TTS)":
        st.info("Premium voice requires Azure Speech Service credentials.")
        azure_key = st.text_input("Azure Speech API Key:", type="password", 
                                 value=os.getenv('AZURE_SPEECH_KEY', ''))
        azure_region = st.text_input("Azure Speech Region:", 
                                    value=os.getenv('AZURE_SPEECH_REGION', 'eastus'))
        
        if st.button("Save Settings"):
            # Create .env file if it doesn't exist
            with open(".env", "w") as env_file:
                env_file.write(f"AZURE_SPEECH_KEY={azure_key}\n")
                env_file.write(f"AZURE_SPEECH_REGION={azure_region}\n")
            os.environ["AZURE_SPEECH_KEY"] = azure_key
            os.environ["AZURE_SPEECH_REGION"] = azure_region
            st.success("Settings saved successfully!")
    else:
        st.info("Standard voice uses Google's Text-to-Speech service and doesn't require any API keys.")

# Title
st.title("🌍 Text-to-Speech Translator")
st.markdown("---")

# Use the selected TTS engine based on settings
def selected_tts_engine(text, lang):
    if 'voice_quality' in locals() and voice_quality == "Premium (Human-like Azure TTS)":
        return text_to_speech_azure(text, lang)
    else:
        return text_to_speech(text, lang)

with tab1:
    st.header("Text to Speech Translation")
# Input text area
input_text = st.text_area("Enter your text here:", height=150)

# Language selection
col1, col2 = st.columns(2)
with col1:
    source_lang = st.selectbox(
        "Select source language:",
            list(LANGUAGES.keys()),
            format_func=lambda x: LANGUAGES[x],
            index=list(LANGUAGES.keys()).index('en'),
            key="text_source_lang"
    )
with col2:
    target_lang = st.selectbox(
        "Select target language:",
            list(LANGUAGES.keys()),
            format_func=lambda x: LANGUAGES[x],
            index=list(LANGUAGES.keys()).index('fr'),
            key="text_target_lang"
        )
    
    # Voice quality selection for this specific translation
    use_enhanced_voice = st.checkbox("Use enhanced natural voice", value=True, 
                                help="Break text into natural phrases for better intonation")

    if st.button("Translate and Generate Audio", key="text_translate_btn"):
    if input_text:
        with st.spinner("Translating and generating audio..."):
                start_time = time.time()
                
            # Translate text
            translated_text = translate_text(input_text, target_lang)
            st.markdown("### Translation:")
            st.write(translated_text)
            
            # Generate audio for original text
                if use_enhanced_voice:
                    st.markdown("🎙️ *Using enhanced natural voice*")
                    original_audio_path = text_to_speech_improved(input_text, source_lang)
                    translated_audio_path = text_to_speech_improved(translated_text, target_lang)
                else:
            original_audio_path = text_to_speech(input_text, source_lang)
                    translated_audio_path = text_to_speech(translated_text, target_lang)
                
            st.markdown("### Original Audio:")
            st.audio(original_audio_path)
            
            # Generate audio for translated text
            st.markdown("### Translated Audio:")
            st.audio(translated_audio_path)
            
                # Provide download links
                st.markdown("### Download Audio Files")
                col1, col2 = st.columns(2)
                
                with col1:
                    original_filename = f"original_{source_lang}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
                    st.markdown(get_download_link(original_audio_path, original_filename), unsafe_allow_html=True)
                
                with col2:
                    translated_filename = f"translated_{target_lang}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
                    st.markdown(get_download_link(translated_audio_path, translated_filename), unsafe_allow_html=True)
                
                # Add to history
                process_time = round(time.time() - start_time, 2)
                st.session_state.history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "original_text": input_text,
                    "translated_text": translated_text,
                    "source_lang": LANGUAGES[source_lang],
                    "target_lang": LANGUAGES[target_lang],
                    "process_time": process_time,
                    "type": "text",
                    "enhanced_voice": use_enhanced_voice
                })
                
                # Display processing time
                st.info(f"Processing completed in {process_time} seconds")
                
                # Clean up temporary files (do this in finally block to ensure cleanup)
            os.unlink(original_audio_path)
            os.unlink(translated_audio_path)
    else:
        st.warning("Please enter some text to translate.") 

with tab2:
    st.header("Speech to Text Translation")
    
    # Language selection for speech
    col1, col2 = st.columns(2)
    with col1:
        speech_source_lang = st.selectbox(
            "Select source language for speech:",
            list(LANGUAGES.keys()),
            format_func=lambda x: LANGUAGES[x],
            index=list(LANGUAGES.keys()).index('en'),
            key="speech_source_lang"
        )
    with col2:
        speech_target_lang = st.selectbox(
            "Select target language for translation:",
            list(LANGUAGES.keys()),
            format_func=lambda x: LANGUAGES[x],
            index=list(LANGUAGES.keys()).index('fr'),
            key="speech_target_lang"
        )
    
    # Voice quality selection for speech translation
    use_enhanced_voice_speech = st.checkbox("Use enhanced natural voice for translation", value=True,
                                         help="Break text into natural phrases for better intonation")
    
    # Upload audio file
    uploaded_file = st.file_uploader("Upload an audio file (WAV, MP3, etc.)", type=["wav", "mp3", "ogg"])
    
    if uploaded_file is not None:
        st.audio(uploaded_file)
        
        if st.button("Transcribe and Translate", key="transcribe_btn"):
            with st.spinner("Transcribing audio..."):
                start_time = time.time()
                
                # Process audio file
                audio_bytes = uploaded_file.read()
                
                # Transcribe audio
                transcribed_text = speech_to_text(audio_bytes, speech_source_lang)
                
                if "Error" in transcribed_text:
                    st.error(transcribed_text)
                else:
                    st.markdown("### Transcribed Text:")
                    st.write(transcribed_text)
                    
                    # Translate transcribed text
                    with st.spinner("Translating text..."):
                        translated_text = translate_text(transcribed_text, speech_target_lang)
                        st.markdown("### Translated Text:")
                        st.write(translated_text)
                        
                        # Generate audio for translated text
                        if use_enhanced_voice_speech:
                            st.markdown("🎙️ *Using enhanced natural voice*")
                            translated_audio_path = text_to_speech_improved(translated_text, speech_target_lang)
                        else:
                            translated_audio_path = text_to_speech(translated_text, speech_target_lang)
                            
                        st.markdown("### Translated Audio:")
                        st.audio(translated_audio_path)
                        
                        # Provide download link
                        translated_filename = f"translated_{speech_target_lang}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
                        st.markdown(get_download_link(translated_audio_path, translated_filename), unsafe_allow_html=True)
                        
                        # Add to history
                        process_time = round(time.time() - start_time, 2)
                        st.session_state.history.append({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "original_text": transcribed_text,
                            "translated_text": translated_text,
                            "source_lang": LANGUAGES[speech_source_lang],
                            "target_lang": LANGUAGES[speech_target_lang],
                            "process_time": process_time,
                            "type": "speech",
                            "enhanced_voice": use_enhanced_voice_speech
                        })
                        
                        # Display processing time
                        st.info(f"Processing completed in {process_time} seconds")
                        
                        # Clean up temporary files
                        os.unlink(translated_audio_path)

with tab3:
    st.header("Translation History")
    
    if not st.session_state.history:
        st.info("No translation history yet. Try translating something!")
    else:
        # Add filter for history type
        history_filter = st.radio("Filter history by:", ["All", "Text translations", "Speech transcriptions", "Enhanced voice", "Standard voice"], horizontal=True)
        
        filtered_history = st.session_state.history
        if history_filter == "Text translations":
            filtered_history = [item for item in st.session_state.history if item.get("type") == "text"]
        elif history_filter == "Speech transcriptions":
            filtered_history = [item for item in st.session_state.history if item.get("type") == "speech"]
        elif history_filter == "Enhanced voice":
            filtered_history = [item for item in st.session_state.history if item.get("enhanced_voice") == True]
        elif history_filter == "Standard voice":
            filtered_history = [item for item in st.session_state.history if item.get("enhanced_voice") == False]
        
        for i, item in enumerate(reversed(filtered_history)):
            type_icon = "📝" if item.get("type") == "text" else "🎤"
            voice_icon = "🎙️" if item.get("enhanced_voice") else "🔊"
            with st.expander(f"{type_icon} {voice_icon} {item['timestamp']} - {item['source_lang']} to {item['target_lang']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Original Text:**")
                    st.write(item["original_text"])
                
                with col2:
                    st.markdown("**Translated Text:**")
                    st.write(item["translated_text"])
                
                st.text(f"Processing time: {item['process_time']} seconds")
                
        if st.button("Clear History"):
            st.session_state.history = []
            st.experimental_rerun()

with tab5:
    st.header("About This App")
    
    st.markdown("""
    <div class="info-box">
    <p>⚠️ <b>Note sur FFmpeg:</b> Pour une meilleure qualité audio, veuillez installer FFmpeg sur votre système.
    Téléchargez-le depuis <a href="https://ffmpeg.org/download.html" target="_blank">ffmpeg.org</a> ou utilisez la commande:</p>
    <code>winget install -e --id Gyan.FFmpeg</code>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    Cette application de traduction texte-parole vous permet de:
    
    * Traduire du texte entre 10 langues différentes
    * Convertir la parole en texte et la traduire
    * Générer de l'audio pour le texte original et traduit
    * Utiliser une voix améliorée avec une meilleure intonation naturelle
    * Télécharger les fichiers audio générés
    * Consulter votre historique de traduction
    
    ### Comment utiliser
    **Traduction de texte:**
    1. Entrez votre texte dans la zone de texte
    2. Sélectionnez les langues source et cible
    3. Choisissez la qualité de la voix (standard ou améliorée)
    4. Cliquez sur "Translate and Generate Audio"
    5. Écoutez l'audio ou téléchargez les fichiers
    
    **Parole à texte:**
    1. Téléchargez un fichier audio
    2. Sélectionnez la langue source de la parole et la langue cible pour la traduction
    3. Choisissez la qualité de la voix pour la sortie
    4. Cliquez sur "Transcribe and Translate"
    5. Consultez la transcription, la traduction et écoutez l'audio traduit
    
    ### Technologies utilisées
    * Streamlit pour l'interface web
    * API Google Translate pour les traductions
    * gTTS (Google Text-to-Speech) pour la génération audio standard
    * Traitement audio avancé pour des voix plus naturelles
    * SpeechRecognition pour la conversion parole-texte
    
    ### Remarque sur la confidentialité
    Cette application utilise des services en ligne pour la traduction et la reconnaissance vocale et peut envoyer votre texte/audio à ces services.
    Aucun texte, traduction ou fichier audio n'est stocké de façon permanente sur un serveur.
    """) 
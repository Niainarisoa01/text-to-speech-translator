# Text-to-Speech Translator | Traducteur Texte-Parole

[English](#english) | [Français](#français)

## English

A powerful web application that allows you to translate text and speech between multiple languages, with enhanced text-to-speech capabilities.

### Features

* Text translation between 10 different languages
* Speech-to-text conversion and translation
* Generate audio for both original and translated text
* Enhanced voice with better natural intonation
* Download generated audio files
* View translation history
* Support for Azure Text-to-Speech for premium voice quality

### Requirements

* Python 3.7+
* FFmpeg (for enhanced audio processing)
* Azure Speech Service API key (optional, for premium voices)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Niainarisoa01/text_to_speech_translator.git
cd text_to_speech_translator
```

2. Create a virtual environment and activate it:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install FFmpeg:
* Windows: `winget install -e --id Gyan.FFmpeg`
* macOS: `brew install ffmpeg`
* Linux: `sudo apt-get install ffmpeg`

5. (Optional) Set up Azure Speech Service:
* Create a `.env` file in the project root
* Add your Azure credentials:
```
AZURE_SPEECH_KEY=your_key_here
AZURE_SPEECH_REGION=your_region_here
```

### Usage

Run the application:
```bash
streamlit run app.py
```

## Français

Une application web puissante qui vous permet de traduire du texte et de la parole entre plusieurs langues, avec des capacités améliorées de synthèse vocale.

### Fonctionnalités

* Traduction de texte entre 10 langues différentes
* Conversion parole-texte et traduction
* Génération audio pour le texte original et traduit
* Voix améliorée avec une meilleure intonation naturelle
* Téléchargement des fichiers audio générés
* Consultation de l'historique des traductions
* Support d'Azure Text-to-Speech pour une qualité vocale premium

### Prérequis

* Python 3.7+
* FFmpeg (pour le traitement audio amélioré)
* Clé API Azure Speech Service (optionnel, pour les voix premium)

### Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/Niainarisoa01/text_to_speech_translator.git
cd text_to_speech_translator
```

2. Créer un environnement virtuel et l'activer :
```bash
python -m venv .venv
source .venv/bin/activate  # Sur Windows : .venv\Scripts\activate
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Installer FFmpeg :
* Windows : `winget install -e --id Gyan.FFmpeg`
* macOS : `brew install ffmpeg`
* Linux : `sudo apt-get install ffmpeg`

5. (Optionnel) Configurer Azure Speech Service :
* Créer un fichier `.env` à la racine du projet
* Ajouter vos identifiants Azure :
```
AZURE_SPEECH_KEY=votre_clé_ici
AZURE_SPEECH_REGION=votre_région_ici
```

### Utilisation

Lancer l'application :
```bash
streamlit run app.py
```

## Text Translation
1. Enter your text in the text area
2. Select source and target languages
3. Click "Translate and Generate Audio"
4. Listen to the audio or download the files

## Speech to Text
1. Upload an audio file (WAV, MP3, OGG formats supported)
2. Select the source language of the speech and target language for translation
3. Click "Transcribe and Translate"
4. View the transcription, translation, and listen to the translated audio

## Requirements

- Python 3.7+
- Internet connection for translation and speech recognition services
- Speakers or headphones for audio playback

## Technologies Used
- Streamlit for the web interface
- Google Translate API for translations
- gTTS (Google Text-to-Speech) for audio generation
- SpeechRecognition for speech-to-text conversion 

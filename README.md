# BhaaratAwaaz

BhaaratAwaaz is an offline-capable multilingual audio translation platform for converting educational/eLearning audio between **English, Hindi, and Marathi**.

## Overview

The current audio pipeline performs:

```text
Input Audio
    |
    v
Audio Preprocessing
    |
    v
ASR / Speech-to-Text
    |
    v
IndicTrans2 Translation
    |
    v
Text-to-Speech
    |
    v
Translated WAV Audio
```

### Main technologies

- **PyAV** — audio decoding and normalization
- **Faster-Whisper** — speech recognition
- **IndicTrans2** — translation
- **Indic Parler-TTS** — speech synthesis
- **FastAPI** — HTTP API

## Supported Languages

| Code | Language |
|------|----------|
| `en` | English |
| `hi` | Hindi |
| `mr` | Marathi |

The source language is optional. If it is omitted, Faster-Whisper performs language detection.

---

# 1. Requirements

## Hardware

The current implementation is designed around a Windows laptop with approximately:

- Intel Core i5 11th generation or newer
- Minimum 16 GB RAM
- 512 GB storage
- Windows 11

The current configuration uses CPU inference.

> **Performance note:** TTS is computationally expensive on CPU. Short audio files can still take several minutes to produce the final translated audio.

## Software

Install:

- Python 3.x
- Git
- Internet access for initial dependency/model setup

After the dependencies and models have been downloaded, the application is designed to operate without internet access.

---

# 2. Clone the Repository

```powershell
git clone <REPOSITORY_URL>
cd BhaaratAwaaz
```

Replace `<REPOSITORY_URL>` with the GitHub repository URL.

---

# 3. Create the Python Environment

On Windows:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Verify Python:

```powershell
python --version
```

---

# 4. Install Dependencies

Install runtime dependencies:

```powershell
pip install -r requirements.txt
```

If a development requirements file is provided:

```powershell
pip install -r requirements-dev.txt
```

The project uses PyTorch, Faster-Whisper, Transformers, IndicTrans2, and Indic Parler-TTS, so the installation can take some time.

---

# 5. Model Setup

The application uses several machine-learning models.

## ASR

The current ASR configuration uses:

```text
faster-whisper
Model: medium
Device: CPU
Compute type: INT8
```

The first execution downloads the model if it is not already available in the local Hugging Face cache.

## Translation

IndicTrans2 models are expected under the configured model directory, currently under:

```text
models/audio/
```

The exact path is controlled by `shared/config.py`.

## TTS

The current TTS implementation uses:

```text
ai4bharat/indic-parler-tts
```

The first execution downloads the required model/tokenizer files from Hugging Face.

The TTS model is large, so several GB of disk space may be required.

## Initial setup vs offline operation

Initial setup:

```text
Internet
   |
   +--> Python packages
   |
   +--> Hugging Face models
   |
   v
Local environment + local models
   |
   v
Offline execution
```

Do **not** commit downloaded model weights to GitHub.

---

# 6. Configuration

Runtime configuration is defined in:

```text
shared/config.py
```

Environment variables can override configuration.

Example `.env`:

```env
BAHAARTAWAAZ_ASR_MODEL=medium
BAHAARTAWAAZ_ASR_DEVICE=cpu
BAHAARTAWAAZ_ASR_COMPUTE_TYPE=int8

BAHAARTAWAAZ_TRANSLATION_DEVICE=cpu

BAHAARTAWAAZ_TTS_DEVICE=cpu
```

Do not commit the real `.env` file.

Commit `.env.example` instead.

---

# 7. Project Structure

```text
BhaaratAwaaz/
|
├── api/
│   └── audio.py
|
├── modules/
│   └── audio/
│       ├── preprocessing.py
│       ├── vad.py
│       ├── asr.py
│       ├── translation.py
│       ├── tts.py
│       └── pipeline.py
|
├── shared/
│   ├── config.py
│   └── logging.py
|
├── tests/
│   └── audio/
│       ├── test_preprocessing.py
│       ├── test_vad.py
│       ├── test_asr.py
│       ├── test_translation.py
│       ├── test_tts.py
│       └── test_pipeline.py
|
├── models/
│   └── audio/
|
├── data/
│   ├── input/
│   ├── output/
│   └── temp/
|
├── main.py
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
└── README.md
```

## Module responsibilities

### `preprocessing.py`

Validates and normalizes input audio.

Current normalized output:

```text
WAV
16 kHz
Mono
PCM 16-bit
```

Maximum supported input duration:

```text
30 minutes
```

### `vad.py`

Contains VAD-related functionality. The ASR stage also uses Faster-Whisper's integrated VAD filtering.

### `asr.py`

Uses Faster-Whisper to convert speech into timestamped text segments.

### `translation.py`

Uses IndicTrans2 to translate recognized text into the requested target language.

### `tts.py`

Uses Indic Parler-TTS to convert translated text into speech and save a WAV file.

### `pipeline.py`

Connects the complete processing flow:

```text
Preprocessing
      ↓
ASR
      ↓
Translation
      ↓
TTS
      ↓
Output JSON + WAV
```

### `api/audio.py`

Provides the FastAPI endpoint for uploading audio and receiving translated audio.

### `main.py`

Creates the FastAPI application and registers the audio router.

---

# 8. Test the Individual Components

Run commands from the project root.

### Preprocessing

```powershell
python -m tests.audio.test_preprocessing
```

### VAD

```powershell
python -m tests.audio.test_vad
```

### ASR

```powershell
python -m tests.audio.test_asr
```

### Translation

```powershell
python -m tests.audio.test_translation
```

### TTS

```powershell
python -m tests.audio.test_tts
```

### Complete pipeline

```powershell
python -m tests.audio.test_pipeline
```

The complete pipeline should generate output similar to:

```text
data/output/test_translation.json
data/output/test_en.wav
```

when the test is configured for English output.

---

# 9. Run the FastAPI Server

From the project root:

```powershell
uvicorn main:app --reload
```

The server should be available at:

```text
http://127.0.0.1:8000
```

---

# 10. Health Checks

Open:

```text
http://127.0.0.1:8000/
```

Expected:

```json
{
  "service": "BhaaratAwaaz",
  "status": "running"
}
```

Health endpoint:

```text
http://127.0.0.1:8000/health
```

Expected:

```json
{
  "status": "healthy"
}
```

---

# 11. Swagger UI

FastAPI provides interactive API documentation.

Open:

```text
http://127.0.0.1:8000/docs
```

Find:

```text
POST /audio/translate
```

Click **Try it out**.

---

# 12. Audio Translation Endpoint

## Endpoint

```text
POST /audio/translate
```

## Form fields

### `audio_file`

Required.

Current supported formats include:

```text
.wav
.mp3
.m4a
.flac
.ogg
.aac
```

### `target_language`

Required.

Allowed values:

```text
en
hi
mr
```

### `source_language`

Optional.

Allowed values:

```text
en
hi
mr
```

If omitted, Faster-Whisper attempts to detect the source language.

---

# 13. Using Swagger

1. Start the server:

```powershell
uvicorn main:app --reload
```

2. Open:

```text
http://127.0.0.1:8000/docs
```

3. Expand:

```text
POST /audio/translate
```

4. Click **Try it out**.

5. Select an audio file.

6. Set the target language, for example:

```text
target_language = en
```

7. Optionally set:

```text
source_language = mr
```

8. Click **Execute**.

The complete pipeline runs:

```text
Audio
 ↓
ASR
 ↓
Translation
 ↓
TTS
```

The endpoint returns the generated WAV audio.

---

# 14. Example Request

Using `curl`:

```bash
curl -X POST "http://127.0.0.1:8000/audio/translate" ^
  -F "audio_file=@data/input/test.wav" ^
  -F "source_language=mr" ^
  -F "target_language=en" ^
  --output translated.wav
```

For Windows/PowerShell, Swagger UI at `/docs` is recommended for the simplest file-upload test.

---

# 15. API Output

The endpoint returns the translated audio as:

```text
audio/wav
```

For example:

```text
translated_test.wav
```

The pipeline also writes a JSON result under:

```text
data/output/
```

The JSON contains information about:

- input audio
- normalized audio
- ASR model/device
- detected source language
- language probability
- translation source/target languages
- translated segments
- TTS output
- final output audio

Example structure:

```json
{
  "audio_file": "...",
  "normalized_audio": {
    "file": "...",
    "sample_rate": 16000,
    "channels": 1,
    "format": "wav"
  },
  "asr": {
    "model": "medium",
    "device": "cpu",
    "compute_type": "int8",
    "language": "mr",
    "language_probability": 0.71
  },
  "translation": {
    "source_language": "mr",
    "target_language": "en"
  },
  "tts": {
    "language": "en",
    "output_file": "..."
  },
  "output_audio": "...",
  "segments": []
}
```

---

# 16. Example Processing Flow

For Marathi → English:

```text
Marathi Audio
      |
      v
Audio Preprocessing
      |
      v
16 kHz Mono WAV
      |
      v
Faster-Whisper
      |
      v
Marathi Transcript
      |
      v
IndicTrans2
      |
      v
English Translation
      |
      v
Indic Parler-TTS
      |
      v
English WAV Audio
```

---

# 17. Offline Operation

BhaaratAwaaz is designed to support offline processing after initial setup.

Internet access is needed initially for:

- Python package installation
- Hugging Face model downloads
- Any required model files

After setup, the processing pipeline does not depend on an external translation or speech API.

Before moving to a fully offline machine, verify:

```powershell
python -m tests.audio.test_asr
python -m tests.audio.test_translation
python -m tests.audio.test_tts
python -m tests.audio.test_pipeline
```

---

# 18. Performance

The current implementation uses CPU inference.

ASR, translation, and especially TTS are neural-network workloads.

TTS can be significantly slower than real time on CPU. Therefore, a short input audio file may still require several minutes to produce the final translated audio.

This is a current performance limitation of the TTS implementation and is separate from FastAPI overhead.

The FastAPI application creates the pipeline when the application starts, so the models are not intentionally loaded from scratch for every request.

---

# 19. Common Warnings

## Hugging Face symlink warning

You may see:

```text
huggingface_hub cache-system uses symlinks by default...
```

This is common on Windows when symbolic-link support is unavailable.

The warning normally does not prevent model loading.

Possible solutions:

- Enable Windows Developer Mode
- Run the relevant process with administrator privileges

Without symlink support, Hugging Face can still cache the files, but disk usage may be less efficient.

## Flash Attention warning

You may see:

```text
Flash attention 2 is not installed
```

The current CPU configuration does not require Flash Attention 2.

This message does not mean that the pipeline has failed.

## TTS attention-mask warning

You may see:

```text
The attention mask is not set and cannot be inferred
because pad token is same as eos token.
```

The current TTS implementation can still generate audio successfully. This warning should be reviewed as part of future TTS cleanup/optimization.

---

# 20. Generated Files

Runtime files are created under:

```text
data/
├── input/
├── output/
└── temp/
```

These files should not be committed to Git.

Downloaded model weights should also not be committed.

The repository should contain `.gitkeep` files if the empty directory structure needs to be preserved.

---

# 21. Git Guidelines

Do not commit:

```text
.venv/
.env
__pycache__/
*.pyc

downloaded model weights
*.bin
*.safetensors
*.pt
*.pth

generated audio
*.wav

generated output JSON
runtime/temp files
```

Use `.gitignore` to prevent these files from being committed.

---

# 22. Quick Start

For a fresh developer environment:

```powershell
git clone <REPOSITORY_URL>
cd BhaaratAwaaz

python -m venv .venv
.venv\Scriptsctivate

python -m pip install --upgrade pip
pip install -r requirements.txt

python -m tests.audio.test_pipeline

uvicorn main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

Use:

```text
POST /audio/translate
```

to upload an audio file and generate translated speech.

---

# 23. Current Status

Implemented:

- [x] Audio validation
- [x] 30-minute input validation
- [x] Audio normalization
- [x] VAD/ASR processing
- [x] Marathi speech recognition
- [x] Hindi speech recognition
- [x] English speech recognition
- [x] IndicTrans2 translation
- [x] English/Hindi/Marathi target languages
- [x] Text-to-speech
- [x] Final translated WAV generation
- [x] FastAPI endpoint
- [x] Swagger documentation
- [x] Offline-capable processing after setup

Future improvements:

- TTS CPU performance optimization
- GPU optimization
- Production deployment
- Better request/job management for long audio
- Improved cleanup of uploaded/generated files
- More robust API error handling
- Authentication/authorization for non-local deployments
- Production-grade offline model packaging

---

## License

Add the project's applicable license here before publishing the repository.

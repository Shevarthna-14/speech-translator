from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import uuid
import logging
from translator import PortableSpeechTranslator

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
TRANSLATED_FOLDER = 'translated'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TRANSLATED_FOLDER'] = TRANSLATED_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSLATED_FOLDER, exist_ok=True)

translator = PortableSpeechTranslator()

ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'flac', 'm4a'}

logging.basicConfig(level=logging.DEBUG)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    try:
        if 'audio' not in request.files:
            logging.error("No audio part in request")
            return jsonify({'error': 'No audio part'}), 400

        audio = request.files['audio']
        if audio.filename == '':
            logging.error("No audio file selected")
            return jsonify({'error': 'No selected file'}), 400

        if not allowed_file(audio.filename):
            logging.error(f"Unsupported audio format: {audio.filename}")
            return jsonify({'error': 'Unsupported audio format. Allowed: wav, mp3, ogg, flac, m4a'}), 400

        filename = secure_filename(audio.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        audio.save(filepath)

        logging.info(f"Audio file saved to {filepath}")
        return jsonify({
            'message': 'Uploaded successfully!',
            'path': f'/uploads/{unique_name}',
            'relative_path': unique_name
        })
    except Exception as e:
        logging.exception("Error in upload_audio")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/record_audio', methods=['POST'])
@app.route('/record_audio', methods=['POST'])
def record_audio():
    try:
        # Get raw audio data from request body
        audio_data = request.get_data()
        if not audio_data:
            return jsonify({'error': 'No audio data received'}), 400
        
        # Generate a unique filename with .webm extension (or you can convert later)
        filename = f"{uuid.uuid4().hex}_recorded.webm"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save raw binary data to file
        with open(filepath, 'wb') as f:
            f.write(audio_data)
        
        app.logger.info(f"Recorded audio saved to {filepath}")
        
        # Return JSON with file info so frontend can use it
        return jsonify({
            'message': 'Recording saved successfully!',
            'path': f'/uploads/{filename}',
            'relative_path': filename
        })

    except Exception as e:
        app.logger.error(f"Error saving recorded audio: {str(e)}")
        return jsonify({'error': 'Failed to save recorded audio.'}), 500


@app.route('/translate_audio', methods=['POST'])
def translate_audio():
    try:
        data = request.get_json()
        if not data or 'audio_path' not in data or 'target_language' not in data:
            logging.error("Missing audio_path or target_language in request")
            return jsonify({'error': 'Missing audio path or target language'}), 400

        filename = os.path.basename(data['audio_path'])
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        lang = data['target_language']

        if not os.path.exists(file_path):
            logging.error(f"Audio file not found: {file_path}")
            return jsonify({'error': 'Audio file not found'}), 404

        logging.info(f"Starting translation for file: {file_path} to language: {lang}")

        result = translator.process_speech(file_path, lang)
        if result is None:
            logging.error("Translation processing returned None")
            return jsonify({'error': 'Translation failed'}), 500

        logging.info(f"Translation success: {result}")

        return jsonify(result)
    except Exception as e:
        logging.exception("Error in translate_audio")
        return jsonify({'error': f'Translation error: {str(e)}'}), 500


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/translated/<filename>')
def translated_file(filename):
    return send_from_directory(app.config['TRANSLATED_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)

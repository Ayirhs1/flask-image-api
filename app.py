from flask import Flask, request, jsonify
import base64
import os
from werkzeug.utils import secure_filename
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)

UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return '<form method="post" action="/upload" enctype="multipart/form-data"><input type="file" name="file"><input type="submit"></form>'

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part in the request.'
    file = request.files['file']
    if file.filename == '':
        return 'No file selected for uploading.'
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Open the file to read it's binary data and then encode it to base64
        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        # Ensure that data is actually being encoded
        if not encoded_string:
            return 'Failed to encode image data.'

        # Prepare the data for the API call
        data = {
            "model": "llava:7b-v1.6-mistral-q5_K_M",
            "prompt": "What is in this picture?",
            "stream": False,
            "images": [encoded_string]
        }
        
        # API endpoint
        api_url = 'http://8.12.5.48:11434/api/generate'
        

        session = requests.Session()
        retries = Retry(total=5,
                        backoff_factor=0.1,
                        status_forcelist=[500, 502, 503, 504])

        session.mount('http://', HTTPAdapter(max_retries=retries))

        try:
            response = session.post(api_url, json=data, timeout=20)
            response.raise_for_status()  # This will help to catch HTTP error codes.
        except requests.exceptions.RequestException as e:
            return f'API request failed: {str(e)}'


    return 'File successfully uploaded but no image data was sent to the API.'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)

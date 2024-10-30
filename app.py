import os
from flask import Flask, render_template, request, jsonify, send_file
from pdf2docx import Converter
import requests
import tempfile

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_pdf_to_word():
    # Check if a file was uploaded
    pdf_file = request.files.get('pdf_file')
    pdf_url = request.form.get('pdf_url')

    if pdf_file and pdf_file.filename != '':
        # Handle file upload
        original_pdf_filename = pdf_file.filename
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf_file:
            pdf_file.save(temp_pdf_file.name)
            temp_pdf_path = temp_pdf_file.name
    elif pdf_url:
        # Handle URL download
        response = requests.get(pdf_url)
        if response.status_code != 200:
            return jsonify({"error": "Failed to download PDF from URL"}), 400

        original_pdf_filename = os.path.basename(pdf_url)  # Get the filename from the URL
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf_file:
            temp_pdf_file.write(response.content)
            temp_pdf_path = temp_pdf_file.name
    else:
        return jsonify({"error": "No PDF file or URL provided"}), 400

    # Convert PDF to DOCX
    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_word_file:
        word_path = temp_word_file.name
        cv = Converter(temp_pdf_path)
        cv.convert(word_path, start=0, end=None)
        cv.close()

    os.remove(temp_pdf_path)

    # Generate the converted document name
    converted_filename = os.path.splitext(original_pdf_filename)[0] + ".docx"
    response = send_file(word_path, as_attachment=True, download_name=converted_filename)

    @response.call_on_close
    def cleanup():
        os.remove(word_path)

    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

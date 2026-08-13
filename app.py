from flask import Flask, request, jsonify, send_from_directory
import os
from omr import omr_calculation
from werkzeug.utils import secure_filename

app = Flask(__name__)

static_dir = os.path.join(os.path.dirname(__file__), 'static')
os.makedirs(os.path.join(static_dir, 'omr_sheets'), exist_ok=True)
os.makedirs(os.path.join(static_dir, 'answer_sheet'), exist_ok=True)
os.makedirs(os.path.join(static_dir, 'result'), exist_ok=True)
app.config['UPLOAD_FOLDER'] = static_dir


def clear_folder(folder_path):
    if not os.path.exists(folder_path):
        return
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isfile(item_path):
            os.remove(item_path)


@app.route('/')
def index():
    return send_from_directory('.', 'main.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file1' in request.files:
        files = request.files.getlist('file1')
        if not files or all(not file.filename for file in files):
            return jsonify({'message': 'No selected image file'}), 400

        sheet_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'omr_sheets')
        clear_folder(sheet_dir)

        for file1 in files:
            if file1.filename:
                filename1 = secure_filename(file1.filename)
                file1.save(os.path.join(sheet_dir, filename1))

        return jsonify({'message': 'Answer sheets uploaded successfully'}), 200

    if 'file2' in request.files:
        file2 = request.files['file2']
        if not file2.filename:
            return jsonify({'message': 'No selected CSV file'}), 400

        key_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'answer_sheet')
        clear_folder(key_dir)
        filename2 = secure_filename(file2.filename)
        file2.save(os.path.join(key_dir, filename2))

        return jsonify({'message': 'Answer key uploaded successfully'}), 200

    return jsonify({'message': 'No file part'}), 400


@app.route('/load')
def load_file():
    results, filepath = omr_calculation()
    messages = []
    for i, result in enumerate(results):
        student_index = i + 1
        messages.append(f'student {student_index} got {result} out of 100')
    return jsonify({'messages': messages, 'filepath': filepath}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

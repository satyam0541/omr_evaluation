from flask import Flask, request, jsonify, send_from_directory
import os
from omr import omr_calculation
from werkzeug.utils import secure_filename
app = Flask(__name__)

static_dir = os.path.join(os.path.dirname(__file__), 'static')
app.config['UPLOAD_FOLDER'] = static_dir
@app.route('/')
def index():
    return send_from_directory('.', 'write-blog.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file1' in request.files:
        #file1 = request.files['file1']
        files = request.files.getlist('file1')
        for file1 in files:
            if file1.filename == '':
                return jsonify({'message': 'No selected file'}), 400
            if file1:
                #filename1 = 'omr_sheet.jpg'
                filename1 =secure_filename(file1.filename)
                file1.save(os.path.join(app.config['UPLOAD_FOLDER'],'omr_sheets', filename1))
        return jsonify({'message': 'File1 uploaded successfully'}),200
    elif 'file2' in request.files:
        file2 = request.files['file2']
        if file2.filename == '':
            return jsonify({'message': 'No selected file'}), 400
        if file2:
            filename2 =secure_filename(file2.filename)
            file2.save(os.path.join(app.config['UPLOAD_FOLDER'],'answer_sheet', filename2))
            return jsonify({'message': 'File2 uploaded successfully'})
    else:
        return jsonify({'message': 'No file part'}), 400
@app.route('/load')
def load_file():
    results,filepath= omr_calculation()  # Assuming omr_calculation() returns a list of student results
    messages = []
    for i, result in enumerate(results):
        student_index = i + 1
        message = 'student {} got {} out of 100'.format(student_index, result)
        messages.append(message)
    return jsonify({'messages': messages , 'filepath': filepath}), 200

if __name__ == '__main__':
    app.run(debug=True)

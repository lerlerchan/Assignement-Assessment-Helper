from flask import Flask, render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Needed for flash messages
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    assignment = request.files.get('assignment')
    rubric = request.files.get('rubric')

    if not assignment or not rubric:
        flash('Both files are required.')
        return redirect(url_for('index'))

    if not (allowed_file(assignment.filename) and allowed_file(rubric.filename)):
        flash('Only PDF files are allowed.')
        return redirect(url_for('index'))

    assignment_filename = secure_filename(assignment.filename)
    rubric_filename = secure_filename(rubric.filename)

    assignment.save(os.path.join(app.config['UPLOAD_FOLDER'], assignment_filename))
    rubric.save(os.path.join(app.config['UPLOAD_FOLDER'], rubric_filename))

    flash('Files uploaded successfully!')
    # TODO: Pass to OCR/LLM pipeline
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

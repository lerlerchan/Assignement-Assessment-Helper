# app.py

from flask import Flask, render_template, request
import os
from werkzeug.utils import secure_filename
from pdf_utils import extract_text_and_tables

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        assignment = request.files.get('assignment')
        rubric = request.files.get('rubric')

        if assignment and allowed_file(assignment.filename):
            filename = secure_filename(assignment.filename)
            assignment_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            assignment.save(assignment_path)

            # 🔍 Extract text and tables
            text, tables = extract_text_and_tables(assignment_path)

            return render_template('result.html', text=text, tables=tables)

    return render_template('index.html')


app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, Flask!'

if __name__ == '__main__':
    app.run(debug=True)
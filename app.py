from flask import Flask, render_template, flash, request, redirect, url_for, send_from_directory, abort
from werkzeug.utils import secure_filename
import os, csv, app
from os.path import join, dirname, realpath

UPLOAD_FOLDER = dirname(realpath(__file__))

app = Flask(__name__)
app.config['UPLOAD_EXTENSIONS'] = ['.csv']
app.config['UPLOAD_PATH'] = UPLOAD_FOLDER

def find_csv_filenames( path_to_dir, suffix=".csv" ):
    filenames = os.listdir(path_to_dir)
    return [ filename for filename in filenames if filename.endswith( suffix ) ]

@app.route('/')
def index():
    files = find_csv_filenames(UPLOAD_FOLDER)
    return render_template('index.html', data=files)

@app.route('/', methods=['POST'])
def upload_file():
    if "file" in request.files:
        uploaded_file = request.files['file']
        filename = secure_filename(uploaded_file.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)
            uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
    if "reset" in request.form:
        for file in find_csv_filenames(UPLOAD_FOLDER):
            remove(file)
    return redirect(url_for('index'))
        
def remove(file_id):
    return os.remove(os.path.join(UPLOAD_FOLDER, file_id))

# def get_data():
#     data = []
#     if 

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     data = []
#     if request.method == 'POST':
#         if request.files:
#             uploaded_file = request.files['filename'] # This line uses the same variable and worked fine
#             filepath = os.path.join(app.config['FILE_UPLOADS'], uploaded_file.filename)
#             uploaded_file.save(filepath)
#             with open(filepath) as file:
#                 csv_file = csv.reader(file)
#                 for row in csv_file:
#                     data.append(row)
#     return render_template('index.html', data=data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

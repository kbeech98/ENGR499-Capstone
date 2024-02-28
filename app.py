from flask import Flask, render_template, flash, request, redirect, url_for, send_from_directory, abort
from werkzeug.utils import secure_filename
import os, csv, app
from os.path import join, dirname, realpath
import pickle
import pandas as pd
import numpy as np

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

@app.route('/results', methods=['POST'])
def get_results():
    if "predict" in request.form:
        process_prediction()

    return render_template('results.html')
        
def remove(file_id):
    return os.remove(os.path.join(UPLOAD_FOLDER, file_id))

def get_dataFrame(csv_filename):
    df = pd.read_csv(os.path.join(app.config['UPLOAD_PATH'], csv_filename))
    return df

def process_prediction():
    csv_file = find_csv_filenames(UPLOAD_FOLDER)
    if csv_file:
        df = get_dataFrame(csv_file[0])

        # Calculate velocity magnitude
        vel_x = np.array(df['velocity_X'])
        vel_y = np.array(df['velocity_Y'])
        vel_z = np.array(df['velocity_Z'])
        vel_mag = np.sqrt(np.square(vel_x) + np.square(vel_y) + np.square(vel_z))
        df['vel_mag'] = vel_mag
        vel_matrix = np.zeros((len(vel_x),3))
        vel_matrix[:,0] = vel_x
        vel_matrix[:,1] = vel_y
        vel_matrix[:,2] = vel_z

        # Calculate gforce magnitude
        g_x = np.array(df['gforce_X'])
        g_y = np.array(df['gforce_Y'])
        g_z = np.array(df['gforce_Z'])
        g_mag = np.sqrt(np.square(g_x) + np.square(g_y) + np.square(g_z))
        df['g_mag'] = g_mag
        gforce_matrix = np.zeros((len(vel_x),3))
        gforce_matrix[:,0] = g_x
        gforce_matrix[:,1] = g_y
        gforce_matrix[:,2] = g_z

        # Project acceleration vector onto velocity vector
        long_g = np.zeros(len(g_x))
        for i in range(len(g_x)):
            long_g[i] = np.dot(gforce_matrix[i,:],vel_matrix[i,:])/vel_mag[i]
            

    return 


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

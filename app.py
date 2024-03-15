from flask import Flask, render_template, flash, request, redirect, url_for, send_from_directory, abort
from werkzeug.utils import secure_filename
import os, csv, app
from os.path import join, dirname, realpath
import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.switch_backend('agg')

UPLOAD_FOLDER = dirname(realpath(__file__))

app = Flask(__name__)
app.config['UPLOAD_EXTENSIONS'] = ['.csv']
app.config['UPLOAD_PATH'] = UPLOAD_FOLDER

@app.route('/')
def index():
    #reset home page
    reset()
    return render_template('index.html')

@app.route('/results', methods=['POST'])
def get_results():
    if "file" in request.files:
        uploaded_file = request.files['file']
        filename = secure_filename(uploaded_file.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)
            uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
            if "predict" in request.form:
                process_prediction(filename)
    return render_template('results.html')

def find_input_file(path_to_dir, suffix=".csv" ):
    filenames = os.listdir(path_to_dir)
    return [ filename for filename in filenames if filename.endswith( suffix ) ]

def find_plots(suffix=".png"):
    plots = os.path.join(UPLOAD_FOLDER,'\static')
    return [ plot for plot in plots if plot.endswith( suffix ) ]

def find_predicted(suffix=".csv"):
    predicted = os.path.join(UPLOAD_FOLDER,'\static')
    return [ prediction for prediction in predicted if prediction.endswith( suffix ) ]

def reset():
    #clear uploaded csv files
    for file in find_input_file(UPLOAD_FOLDER):
        remove_file(file)
    #clear plots
    clear_plots()
    #clear predicted temp
    clear_predicted()

def clear_plots():
    #clear plots
    for plot in find_plots():
        remove_plot(plot)

def clear_predicted():
    for predicted in find_predicted():
        remove_predicted_temp_csv(predicted)

def remove_file(file_id):
    return os.remove(os.path.join(UPLOAD_FOLDER, file_id))

def remove_plot(plot_id):
    return os.remove(os.path.join(UPLOAD_FOLDER, '\static', plot_id))

def remove_predicted_temp_csv(predicted_temp_id):
    return os.remove(os.path.join(UPLOAD_FOLDER, '\static', predicted_temp_id))

def get_dataFrame(csv_filename):
    df = pd.read_csv(os.path.join(app.config['UPLOAD_PATH'], csv_filename))
    return df

def process_prediction(csv_filename):
    if csv_filename:
        #load model 
        model = pickle.load(open(os.path.join(UPLOAD_FOLDER, 'models/finalized_model_linear.sav'), 'rb'))

        #load testing data
        df = get_dataFrame(csv_filename)

        # Calculate velocity magnitude
        vel_x = np.array(df['velocity_X'])
        vel_y = np.array(df['velocity_Y'])
        vel_z = np.array(df['velocity_Z'])
        vel_mag = np.sqrt(np.square(vel_x) + np.square(vel_y) + np.square(vel_z))
        df['vel_mag'] = vel_mag

        # Angular Velocity
        ang_x = np.array(df['angular_vel_X'])
        ang_y = np.array(df['angular_vel_Y'])
        ang_z = np.array(df['angular_vel_Z'])
        ang_mag = np.sqrt(np.square(ang_x) + np.square(ang_y) + np.square(ang_z))
        df['ang_mag'] = ang_mag
        vel_matrix = np.zeros((len(vel_x),3))
        vel_matrix[:,0] = vel_x
        vel_matrix[:,1] = vel_y
        vel_matrix[:,2] = vel_z

        # Time and Change in Time
        lap_time = df['lap_time']
        length_lap = len(lap_time)
        prev_lap_time = np.zeros(length_lap) 
        prev_lap_time[0] = df['lap_time'][0]
        prev_lap_time[1:] = df['lap_time'][0:length_lap-1]

        change_in_time = np.zeros(length_lap)
        change_in_time[:] = lap_time[:] -prev_lap_time[:]

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

        df['longitudinal_gforce'] = long_g
        brake_temp_1 = np.array(df['brake_temp_1'])
        #brake_temp_1 = array.reshape(-1, 1)
        length = len(brake_temp_1)
        prev_temp_1 = np.zeros(length)
        prev_temp_1[0] = df['brake_temp_1'][0]
        prev_temp_1[1:] = df['brake_temp_1'][0:length-1] 

        testing_features = np.zeros((167256,24))
        #testing_features = np.zeros((2902,3))
        testing_features[:,0] = prev_temp_1 #[df['lapNum']]
        testing_features[:,1] = long_g #[df['lapNum']]
        testing_features[:,2] = vel_mag #[df['lapNum']]
        testing_features[:,3] = vel_x #[df['lapNum']]
        testing_features[:,4] = vel_y #[df['lapNum']]
        testing_features[:,5] = vel_z #[df['lapNum']]
        testing_features[:,6] = g_mag #[df['lapNum']]
        testing_features[:,7] = g_x #[df['lapNum']]
        testing_features[:,8] = g_y #[df['lapNum']]
        testing_features[:,9] = g_z #[df['lapNum']]
        testing_features[:,10] = ang_x #[df['lapNum']]
        testing_features[:,11] = ang_y #[df['lapNum']]
        testing_features[:,12] = ang_z #[df['lapNum']]
        testing_features[:,13] = ang_mag #[df['lapNum']]
        testing_features[:,14] = prev_lap_time #[df['lapNum']]
        testing_features[:,15] = vel_x * vel_x #[df['lapNum']]  * vel_x[df['lapNum']]
        testing_features[:,16] = vel_x * g_x #[df['lapNum']] * g_x[df['lapNum']]
        testing_features[:,17] = vel_x * ang_x #[df['lapNum']] * ang_x[df['lapNum']]
        testing_features[:,18] = vel_x * long_g #[df['lapNum']] * long_g[df['lapNum']]
        testing_features[:,19] = g_x * g_x #[df['lapNum']] * g_x[df['lapNum']]
        testing_features[:,20] = g_x * ang_x #[df['lapNum']] * ang_x[df['lapNum']]
        testing_features[:,21] = prev_temp_1 * long_g #[df['lapNum']][0] * long_g[df['lapNum']]
        testing_features[:,22] = prev_temp_1 * vel_x #[df['lapNum']][0] * long_g[df['lapNum']]
        testing_features[:,23] = prev_temp_1 * g_x #[df['lapNum']][0] * long_g[df['lapNum']]

        for i in range(0,167255):
            testing_features[i+1,0] = model.predict(testing_features[i, :].reshape(1,-1))
        predicted_temp = testing_features[:,0]
        
        #generate heatflux data (create prev_temp, change_temp arrays)
        predicted_temp_prev = np.zeros(length_lap)
        predicted_temp_prev[1:] = predicted_temp[:167255]
        change_in_temp = np.zeros(length_lap)
        change_in_temp[1:] = predicted_temp[:167255] -predicted_temp_prev[:167255]


        m = 1
        c = 1
        A = 1
        heatflux = np.zeros(length_lap)
        heatflux[:] = (m*c*change_in_temp[:])/(change_in_time[:]*A)

        #clear previous plots and predicted temperature
        clear_plots()
        clear_predicted()

        #generate new plot 
        plt. clf() 
        fig1 = plt.figure()
        x_points = (np.arange(sum(df['lapNum'] == 15)))
        plt.plot(x_points, predicted_temp[df['lapNum'] == 15], label='Predicted Temperature')
        plt.legend()
        plt.title('Brake Temperature over one lap')
        plt.xlabel('Samples (Will be converted to distance)')
        plt.ylabel('Brake Rotor Temperature (*C)')
        plt.savefig('static\Predicted_temp_plt.png')
        fig2 = plt.figure()
        x_points = (np.arange(sum(df['lapNum'] == 15)))
        plt.plot(x_points, heatflux[df['lapNum'] == 15], label='HeatFlux')
        plt.legend()
        plt.title('HeatFlux over one lap')
        plt.xlabel('Samples (Will be converted to distance)')
        plt.ylabel('Units idk')
        plt.savefig('static\heat_flux.png')



        #generate predicted temperature data csv 
        predicted_temp_df = pd.DataFrame(predicted_temp)
        predicted_temp_df.to_csv("static/predicted_temp.csv")



        #output predicted temperature important features/characteristics (max/min temp, average.. ect)

    return

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    text = ""
    data = []
    if request.method == 'POST':
        if request.files:
            uploaded_file = request.files['file']
            uploaded_file.save(os.path.join(app.config['FileUp'], uploaded_file.files))
            f = request.form['filename']
            with open(f) as files:
                csv_file = csv.reader(file)
                for row in csv_file:
                    data.append(row)
                return redirect(request.url)
        text = request.form.get('avatar')
    return render_template('index.html', text=filename)

app.config['FILE_UPLOADS'] = "C:\Users\Jonathan\Downloads"
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

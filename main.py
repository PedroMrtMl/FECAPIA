from mediacode import main
from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        remedio = request.form.get('remedio')
        result = main(remedio)
    return render_template('index.html', result=result)

@app.route('/hello', methods=['GET'])
def HelloWorld():
    return 'Hello World'

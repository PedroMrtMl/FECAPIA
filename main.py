from mycode import function
from flask import Flask, request, render_template


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        sl = float(request.form.get('sl'))
        sw = float(request.form.get('sw')) 
        pl = float(request.form.get('pl'))
        result = function(sl,sw,pl)
    return render_template('index.html', result=result)



@app.route('/hello', methods=['GET'])
def HelloWorld():
    return 'Hello World'

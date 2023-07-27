from flask import Flask, request, render_template, session, redirect, url_for
import numpy as np
import pickle
import bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)
app.app_context().push()

## open and load the pickle file provided in read mode.
model = pickle.load(open('model.pkl', 'rb'))

app.config['DEBUG'] = True
app.config['ENV'] = 'development'
app.config['FLASK_ENV'] = 'development'
app.config['SECRET_KEY'] = 'ItShouldBeAlongStringOfRandomCharacters'
app.config[
    'SQLALCHEMY_DATABASE_URI'] = 'mysql://root:EtyFetbwLe6iQ6E2vxEJ@containers-us-west-157.railway.app:5757/railway'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

app.config['MYSQL_HOST'] = 'containers-us-west-157.railway.app'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'EtyFetbwLe6iQ6E2vxEJ'
app.config['MYSQL_PORT'] = 5757
app.config['MYSQL_DB'] = 'railway'

mysql = MySQL(app)


class users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(255))
    password = db.Column(db.String(255))

    def __init__(self, user_name, password):
        self.user_name = user_name
        self.password = password


db.create_all()


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO users VALUES (NULL, % s, % s, % s)', (username, hashed_password, email,))
        mysql.connection.commit()
        msg = 'You have successfully registered !'
        return render_template('login.html', msg=msg)
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg=msg)


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE user_name = % s', (username,))
        account = cursor.fetchone()
        if account:
            hashed_password = account['password']
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['user_name']
                msg = 'Logged in successfully !'
                return render_template('predict.html', msg=msg)
            else:
                msg = 'Incorrect username / password !'
    return render_template('login.html', msg=msg)


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        float_features = [float(x) for x in request.form.values()]
        final_features = [np.array(float_features)]
        prediction = model.predict(final_features)

        output = round(prediction[0], 2)

        if prediction == 1:
            output = "Congrats!! You are eligible for the loan."
        else:
            output = "Sorry, You are not eligible for the loan."

            # Render the template with the prediction result and form data
        return render_template('predict.html', prediction_text=output)
    return render_template('predict.html')


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('user_name', None)
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)

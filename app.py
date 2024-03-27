import torch
from flask import Flask, render_template, request, jsonify
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from torch.nn.functional import softmax
from flask import Flask, render_template, request, redirect, url_for
from flask import Flask, session
from flask_mysqldb import MySQL
import mysql.connector
import secrets


app = Flask(__name__)

app.secret_key = secrets.token_hex(16)

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'  # Change this if your MySQL username is different
app.config['MYSQL_PASSWORD'] = ''  # Enter your MySQL password here
app.config['MYSQL_DB'] = 'journal'
mysql = MySQL(app)



# Initialize sentiment analysis model and tokenizer
model_name = "j-hartmann/emotion-english-distilroberta-base"
model = AutoModelForSequenceClassification.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

def analyze_sentiment(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    outputs = model(**inputs)
    predictions = softmax(outputs.logits, dim=-1)
    emotion_scores = {model.config.id2label[i]: score.item() for i, score in enumerate(predictions[0])}
    return emotion_scores

@app.route("/")
def index():
    return redirect(url_for('login'))  # Redirect to the login page

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirmPassword"]

        # Check if email already exists
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user:
            return render_template("signup.html", error="Email already exists")

        if password != confirm_password:
            return render_template("signup.html", error="Passwords do not match")
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('login'))
    return render_template("signup.html", error="")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user:
            if password == user[2]:  
                session['logged_in'] = True
                session['email'] = email
                return redirect(url_for('home'))
            else:
                return render_template("login.html", error="Invalid email/password combination")
        return render_template("login.html", error="Invalid email/password combination")
    return render_template("login.html")

@app.route("/home")
def home():
    if 'logged_in' in session:
        return render_template("home.html")
    else:
        return redirect(url_for('login'))

@app.route("/analysis")
def analysis():
    return render_template("analysis.html")

@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    session.pop('email', None)
    return redirect(url_for('login'))

@app.route("/analyze", methods=["POST"])
def analyze():
 if request.method == 'POST':
        journal_text = request.form['journal']
        sentiments = analyze_sentiment(journal_text)
        
        
        if mysql.connection is None:
         return "Error: Database connection not established"

        cur=mysql.connection.cursor()
        cur.execute("INSERT INTO journalentry (journal_text, sentiments) VALUES (%s, %s)", (journal_text, str(sentiments)))
        mysql.connection.commit()
        cur.close()

        return jsonify({'sentiments': sentiments})

@app.route('/weekly_analysis', methods=['GET'])
def weekly_analysis():
    # Fetch entries from the database
    cur=mysql.connection.cursor()
    cur.execute("SELECT * FROM journalentry ORDER BY id DESC")  
    entries = cur.fetchall()
    cur.close()

    combined_analysis = []

    # Process entries in batches of 7
    for i in range(0, len(entries), 7):
        batch_entries = entries[i:i+7]
        batch_texts = [entry[1] for entry in batch_entries]  # Assuming the text is in the second column
        batch_emotions = [analyze_sentiment(text) for text in batch_texts]
        combined_analysis.append(batch_emotions)
        
        return jsonify(combined_analysis)
    

@app.route("/previous")
def previous():
    if mysql.connection is None:
     return "Error: Database connection not established"
     # Fetch journal entries from the database
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM journalentry ORDER BY id DESC")  # Assuming 'id' is the primary key
    entries = cur.fetchall()
    cur.close()

    # Render the template with the fetched entries
    return render_template('previous.html', entries=entries)
      


if __name__ == '__main__':
    app.run(debug=True)

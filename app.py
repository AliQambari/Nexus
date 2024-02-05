from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import LoginManager, current_user
from flask_mail import Mail, Message
from config import Config
import threading
import vercel_ai
from flask_login import login_required
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db' 
app.config['SECRET_KEY'] = 'NHS76T66^G45#2@H()[-PXX ]XS!!@#$ONC626ssj55a'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
app.config.from_object(Config)
mail = Mail(app)
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    activity_timestamp = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reset_token = db.Column(db.String(100))

    # Implement UserMixin methods

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return '<User %r>' % self.username

    
class Paraphrase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)  # Store the model-generated response
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id, prompt, response=None):
        self.user_id = user_id
        self.prompt = prompt
        self.response = response
        
class Meaning(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(20), nullable=False)
    meaning = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    def __init__(self, word, meaning, user_id):
        self.word = word
        self.meaning = meaning
        self.user_id = user_id
    
class FavoriteWord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(20), nullable=False)
    meaning = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, word, meaning, user_id):
        self.word = word
        self.meaning = meaning
        self.user_id = user_id
#___________________________________________________________

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Define the About route
@app.route('/about')
def about():
    return render_template('about.html')

# Registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address already exists.', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')

        return redirect(url_for('login'))
    return render_template('register.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id  # Set the user as authenticated
            user.activity_timestamp = datetime.utcnow()  # Update the activity timestamp
            db.session.commit()  # Commit the changes to the database
            #flash('Login successful!', 'success')
            if user.username == 'admin':
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('index'))
        else:
            flash( 'Invalid username or password', 'info')
            return render_template('login.html')

    return render_template('login.html')


import secrets
# Password reset page
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']

        user = User.query.filter_by(email=email).first()

        if user:
            # Generate a password reset token
            token = secrets.token_urlsafe(32)  # Generate a secure and random URL-safe token

            # Save the token in the user's database record
            user.reset_token = token
            db.session.commit()

            reset_link = url_for('reset_password_confirm', token=token, _external=True)
            message = f"Click the link below to reset your password:\n{reset_link}"

            msg = Message("Password Reset Request", recipients=[user.email])
            msg.body = message

            mail.send(msg)  # Send the password reset email

            flash('A password reset link has been sent to your email.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid email address.', 'info')
            return redirect(url_for('reset_password'))

    return render_template('reset_password.html')

from werkzeug.security import generate_password_hash

# Password reset confirmation page
@app.route('/reset_password_confirm/<token>', methods=['GET', 'POST'])
def reset_password_confirm(token):
    # Verify the token
    user = User.query.filter_by(reset_token=token).first()
    if not user:
        flash('Invalid or expired token.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password == confirm_password:
            # Update the user's password in the database
            user.password = generate_password_hash(new_password)
            user.reset_token = None  # Reset the token after password change
            db.session.commit()

            flash('Password has been reset successfully!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Passwords do not match.', 'danger')

    return render_template('reset_password_confirm.html', token=token)

# dashboard route

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_authenticated:
        user = User.query.get(current_user.id)
        paraphrases = Paraphrase.query.filter_by(user_id=user.id).all()
        favorite_words = FavoriteWord.query.filter_by(user_id=user.id).all()


        return render_template('dashboard.html', user=user, paraphrases=paraphrases, favorite_words = favorite_words)
    else:
        flash('You must be logged in to access this page.', 'warning')
        return redirect(url_for('login'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

#-------------------------------writing ------------------------------------
#---------------------------------------------------------------------------


client = vercel_ai.Client()
from flask_login import current_user
from flask_login import login_required

## Create a function for text generation
def generate_text_in_background(user_prompt, user_email, user_id):
    with app.app_context():
        client = Client("https://ysharma-explore-llamav2-with-tgi.hf.space/--replicas/ppt5s/")
        prompt = f"""
            "Paraphrase the English sentence '[user_prompt]' using more suitable vocabulary. The paraphrase should maintain the original sentence's intended meaning while being clear and concise."

            ANYTHING BETWEEN ** IS THE CANDIDATE'S WRITING.
            If the sentence has no meaning or is vague, say: "❌The sentence is vague or incorrect. "

            {"*" + user_prompt + "*"}
            """

        try:
            generated_text = ""
            answer_generated = False

            while not answer_generated:
                try:
                    for chunk in client.predict(
                        prompt,
                        "Act as a professional English writer. Don't talk like a person before and after the answer you provide. Only give the answer.",
                        0.6,
                        1024,
                        0.9,
                        1.0,
                        api_name="/chat"
                    ):                        
                        generated_text += chunk
                        answer_generated = True
                except Exception as e:
                    print(f"Retrying...")

            # Save the user's prompt and model-generated response to the database
            paraphrase = Paraphrase(user_id=user_id, prompt=user_prompt, response=generated_text)
            db.session.add(paraphrase)
            db.session.commit()

            """ if user_email and generated_text:
                msg = Message('Correction Response', recipients=[user_email])
                msg.body = f'Your response: {user_prompt}\n\nCorrection:\n{generated_text}'
                mail.send(msg)"""
        except Exception as e:
            print(f"Error: {str(e)}")          

# Route for paraphrasing
@app.route('/paraphrase', methods=['GET', 'POST'])
@login_required
def paraphrase():
    if request.method == 'POST':
        candidate_response = request.form.get('user_prompt')  # Assuming a form field for user input
        user_email = current_user.email  # Retrieve the user's email from Flask-Login
        user_id = current_user.id  # Retrieve the user's email from Flask-Login

        # Create a thread to run text generation in the background
        thread = threading.Thread(target=generate_text_in_background, args=(candidate_response, user_email, user_id))
        thread.daemon = True
        thread.start()
        
        flash('Paraphrasing is in progress. It will soon be available in your dashboard.', 'info')
        
        # Redirect to a confirmation page to prevent form resubmission
        return redirect(url_for('prompt_confirmation'))

    return render_template('paraphrase.html')

# Confirmation page to inform the user that their prompt has been submitted
@app.route('/prompt_confirmation')
def prompt_confirmation():
    return render_template('paraphrase.html')

# Dictionary function
from gradio_client import Client

def dictionary_background(word_to_lookup, user_id):
    client = Client("https://ysharma-explore-llamav2-with-tgi.hf.space/--replicas/ppt5s/")
    prompt = f"""
        "Provide a detailed description for the word between ** including the following: (if the word has
        typo or is written incorrectly, correct it and then answer.)

        Short definition in English.
        Phonetic pronunciation.
        Contextual usage in a sentence.
        All possible meanings.
        An example sentence in English.
        Common collocations or phrases in which this word is typically used."

        {"*" + word_to_lookup + "*"}
    """
    
    try:
        generated_text = ""
        answer_generated = False

        while not answer_generated:
            try:
                for chunk in client.predict(
                    prompt,
                    "Act as a professional dictionary. Don't talk before and after the answer you provide. Only give the answer.",
                    0.6,
                    1024,
                    0.9,
                    1.0,
                    api_name="/chat"
                ):
                    generated_text += chunk
                    answer_generated = True
            except Exception as e:
                print(f"Retrying...")

        return generated_text
    except Exception as e:
        print(f"Error: {str(e)}")

from flask_login import current_user

# Dictionary route
@app.route('/dictionary', methods=['GET', 'POST'])
@login_required
def dictionary():
    global fav
    meaning_text = None  # Initialize meaning_text as None
    favorite_words = []  # Initialize favorite_words as an empty list

    if request.method == 'POST':
        word_to_lookup = request.form.get('word_to_lookup')
        fav = word_to_lookup

        # Ensure that the user is logged in
        if current_user.is_authenticated:
            user_id = current_user.id  # Get the user ID from the current_user object

            # Check if the meaning is already available in the database
            meaning = Meaning.query.filter_by(word=word_to_lookup).first()

            if meaning is None:
                # If the meaning is not available, generate it and store in the database
                meaning_text = dictionary_background(word_to_lookup, user_id)
            else:
                # Meaning is available in the database, no need to fetch it
                meaning_text = meaning.meaning

            # Fetch favorite words for the current user
            favorite_words = FavoriteWord.query.filter_by(user_id=user_id).all()
            #return redirect(url_for('word_confirmation'))

    return render_template('dictionary.html', meaning=meaning_text, favorite_words=favorite_words)

@app.route('/add_to_favorites', methods=['POST'])
@login_required
def add_to_favorites():
    if request.method == 'POST':
        word = fav
        meaning = request.form.get('meaning')
        user_id = current_user.id

        favorite_words = FavoriteWord(word=word, meaning=meaning, user_id=user_id)
        db.session.add(favorite_words)
        db.session.commit()

        flash(f'Added "{word}" to your favorite words.', 'success')

    return redirect(url_for('dictionary'))

@app.route('/remove_favorite', methods=['POST'])
@login_required
def remove_favorite():
    if request.method == 'POST':
        word = request.form.get('word')
        user_id = current_user.id

        favorite_to_remove = FavoriteWord.query.filter_by(word=word, user_id=user_id).first()

        if favorite_to_remove:
            db.session.delete(favorite_to_remove)
            db.session.commit()
            flash(f'Removed "{word}" from your favorite words.', 'success')
        else:
            flash('Word not found in your favorites.', 'danger')

    return redirect(url_for('dashboard'))

@app.route('/remove_paraphrase', methods=['POST'])
@login_required
def remove_paraphrase():
    if request.method == 'POST':
        paraphrase_id = request.form.get('paraphrase_id')
        user_id = current_user.id

        paraphrase_to_remove = Paraphrase.query.filter_by(id=paraphrase_id, user_id=user_id).first()

        if paraphrase_to_remove:
            db.session.delete(paraphrase_to_remove)
            db.session.commit()
            flash('Removed a paraphrase.', 'success')
        else:
            flash('Paraphrase not found.', 'danger')

    return redirect(url_for('dashboard'))
# Import the required modules
from flask_login import login_required
#-------------------------------------------------------translate----------------

# Define the admin route
@app.route('/admin')
@login_required
def admin():
    if current_user.username == 'admin':
        # Query the most recent user by activity_timestamp
        most_recent_user = User.query.order_by(User.activity_timestamp.desc()).first()
        users = User.query.all()
        return render_template('admin.html', users=users, most_recent_user=most_recent_user)
    else:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))
    
# Edit user route
@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get(user_id)
    
    if request.method == 'POST':
        # Handle the form submission to edit user data
        user.username = request.form['new_username']
        user.email = request.form['new_email']
        db.session.commit()
        flash('User data has been updated successfully.', 'success')
    
    return render_template('edit_user.html', user=user)

# View user's dashboard
@app.route('/dashboard/<int:user_id>')
@login_required
def view_dashboard(user_id):
    if current_user.username == 'admin' or current_user.id == user_id:
        user = User.query.get(user_id)
        paraphrases = Paraphrase.query.filter_by(user_id=user.id).all()
        favorite_words = FavoriteWord.query.filter_by(user_id=user.id).all()
        return render_template('dashboard.html', user=user, paraphrases=paraphrases, favorite_words=favorite_words)
    else:
        flash('You do not have permission to access this user\'s dashboard.', 'danger')
        return redirect(url_for('index'))

# Change user's password (admin only)
@app.route('/change_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def change_password(user_id):
    if current_user.username == 'admin':
        user = User.query.get(user_id)

        if request.method == 'POST':
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']

            if new_password == confirm_password:
                # Update the user's password in the database
                user.password = generate_password_hash(new_password)
                db.session.commit()
                flash('Password has been changed successfully!', 'success')
                return redirect(url_for('view_dashboard', user_id=user.id))
            else:
                flash('Passwords do not match.', 'danger')

        return render_template('change_password.html', user=user)
    else:
        flash('You do not have permission to change this user\'s password.', 'danger')
        return redirect(url_for('index'))

from flask import request

# Route to display all words and their meanings
@app.route('/admin/all_words_and_meanings', methods=['GET', 'POST'])
@login_required
def all_words_and_meanings():
    if current_user.username == 'admin':
        if request.method == 'POST':
            # Handle edit and remove actions
            action = request.form.get('action')
            word_id = request.form.get('word_id')

            if action == 'edit':
                # Redirect to the edit word page
                return redirect(url_for('edit_word', word_id=word_id))
            elif action == 'remove':
                # Delete the word and its meaning
                word = Meaning.query.get(word_id)
                db.session.delete(word)
                db.session.commit()
                flash('Word and meaning have been removed.', 'success')

        # Query all words and their meanings from the Meaning table
        words_and_meanings = Meaning.query.all()
        return render_template('all_words_and_meanings.html', words_and_meanings=words_and_meanings)
    else:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))

# Route to edit a word and its meaning
@app.route('/admin/edit_word/<int:word_id>', methods=['GET', 'POST'])
@login_required
def edit_word(word_id):
    if current_user.username == 'admin':
        word = Meaning.query.get(word_id)
        if request.method == 'POST':
            # Handle the form submission to edit the word and meaning
            new_word = request.form['new_word']
            new_meaning = request.form['new_meaning']

            word.word = new_word
            word.meaning = new_meaning
            db.session.commit()
            flash('Word and meaning have been updated.', 'success')

        return render_template('edit_word.html', word=word)
    else:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))

# Route to remove a word and its meaning
@app.route('/admin/remove_word/<int:word_id>', methods=['POST'])
@login_required
def remove_word(word_id):
    if current_user.username == 'admin':
        word = Meaning.query.get(word_id)
        db.session.delete(word)
        db.session.commit()
        flash('Word and meaning have been removed.', 'success')
        return redirect(url_for('all_words_and_meanings'))
    else:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))
from flask import jsonify    
# Updated speaking function
from flask import Flask, render_template, request, jsonify
import vercel_ai
from flask_login import login_required, current_user

# Function to improve transcription
def transcribe_improve(transcription):
    client = Client("https://ysharma-explore-llamav2-with-tgi.hf.space/--replicas/ppt5s/")
    prompt = f"""
            The user speaks and the transcribe is given in *transcription* below. Act as a professional EFL
            teacher that can correct users speaking task and improve them. you should provide
            a better version that is more fluent and natural..Remember to improve
            the grammatical problems or coherence o cohesion problem. Make it more meaningful. But, Try to
            keep the meaning unchangeed as possible.
            
            As well as the respose based on abovementioned requirements, provide another version that you "as a native English speaker" would say.
            Don;t rewrite teh transcription. So you give two responses . 1: Improved Version. 2: Native speaker version.
            Transcription:
            {"*"+ transcription+ "*" }
        """
    
    try:
        generated_text = ""
        answer_generated = False

        while not answer_generated:
            try:
                for chunk in client.predict(
                    prompt,
                    "Act as a efl teacher. Don't talk like a person before and after the answer you provide. Only give the answer.",
                    0.6,
                    1024,
                    0.9,
                    1.0,
                    api_name="/chat"
                ):
                    generated_text += chunk
                    answer_generated = True
            except Exception as e:
                print(f"Retrying...")

        return generated_text
    except Exception as e:
        print(f"Error: {str(e)}")

# Route to improve transcription
@app.route('/speaking', methods=['GET','POST'])
@login_required
def speaking():
    if request.method == 'POST':
        transcription = request.form.get('transcription')

        # Ensure that the user is logged in
        if current_user.is_authenticated:
            improved_transcription = transcribe_improve(transcription)

            return render_template('speaking.html', improved_transcription=improved_transcription)

    return  render_template('speaking.html')

#-----------------
@app.route('/s2t_s2s')
@login_required
def s2t_s2s():
    return render_template('s2t_s2s.html')

@app.route('/t2t_t2s')
@login_required
def t2t_t2s():
    return render_template('t2t_t2s.html')

@app.route('/dictation')
@login_required
def dictation():
    return render_template('dictation.html')
#--------------------
if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        db.create_all()
    app.run(debug=True)


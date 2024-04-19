import random
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from flask_pymongo import PyMongo
from flask_mail import Mail, Message
from pymongo import MongoClient
from werkzeug.utils import secure_filename
import os
import datetime
from bson import Binary, json_util, ObjectId
from bson.json_util import dumps
import uuid
import mimetypes
from gensim import corpora, similarities
from nltk.tokenize import word_tokenize, sent_tokenize
import nltk
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import os
import textwrap
from jinja2 import Environment
from nltk.tokenize import word_tokenize
from gensim.corpora import Dictionary
from gensim.similarities import MatrixSimilarity
from gensim.matutils import sparse2full

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB configuration for user profiles
app.config['MONGO_URI'] = 'mongodb+srv://adarshmishra:1234@messportal.qrkbtya.mongodb.net/Assign-FS'
mongo = PyMongo(app)
collection = mongo.db.profiles
assignments_collection = mongo.db['assignments']
answer_collection = mongo.db['answer']

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Replace with your SMTP server address
app.config['MAIL_PORT'] = 587  # Replace with your SMTP server port (usually 587 for TLS)
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'fittrack2@gmail.com'  # Replace with your email username
app.config['MAIL_PASSWORD'] = 'ksdvgulnzqkcjpgj'  # Replace with your email password
app.config['UPLOAD_FOLDER'] = 'uploads/'
mail = Mail(app)

# Generate OTP
def generate_otp():
    return str(random.randint(1000, 9999))

# Route for Sign Up Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        college_email = request.form['college_email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        phone = request.form['phone']
        user_type = request.form['user_type']
        branch = request.form['branch']  # Get branch from form
        year = request.form['year']  # Get year from form
        URN = request.form['URN']

        # Check if email is already registered
        existing_user = collection.find_one({'college_email': college_email})
        if existing_user:
            return render_template('signup.html', error='Email already exists. Please choose another.')

        # Check if passwords match
        if password != confirm_password:
            return render_template('signup.html', error='Passwords do not match. Please try again.')

        # Generate OTP
        otp = generate_otp()

        # Send OTP to user's email
        msg = Message('Signup - OTP Verification', sender='fittrack2@gmail.com', recipients=[college_email])
        msg.body = f'Your OTP for signup is: {otp}'
        mail.send(msg)

        # Store OTP in session
        session['otp'] = otp

        # Store user data in session
        session['name'] = name
        session['college_email'] = college_email
        session['password'] = password
        session['phone'] = phone
        session['user_type'] = user_type
        session['branch'] = branch  # Store branch in session
        session['year'] = year  # Store year in session
        session['URN']= URN 
        # Redirect to OTP verification page
        return redirect(url_for('verify_signup_otp'))

    return render_template('signup.html')

# Route for OTP Verification Page
@app.route('/verify_signup_otp', methods=['GET', 'POST'])
def verify_signup_otp():
    if request.method == 'POST':
        user_otp = request.form['otp']
        if 'otp' in session and user_otp == session['otp']:
            # OTP verification successful, insert user data into the database
            user_data = {
                'name': session['name'],
                'college_email': session['college_email'],
                'password': session['password'],
                'contact_number': session['phone'],
                'branch': session['branch'],
                'year': session['year'],
                'URN': session['URN'],  # Include URN in user data
                'user_type':session['user_type']
            }
            collection.insert_one(user_data)

            # Clear session data
            session.pop('otp')
            session.pop('name')
            session.pop('college_email')
            session.pop('password')
            session.pop('phone')
            session.pop('branch')
            session.pop('year')
            session.pop('URN')  # Remove URN from session
            session.pop('user_type')
            session.clear()

            # Redirect to login page after successful sign up
            return redirect(url_for('login'))
        else:
            # Incorrect OTP entered, display error message
            error_message = "Incorrect OTP. Please try again."
            return render_template('verify_otp.html', error=error_message)

    return render_template('verify_otp.html')

# Route for Password Reset Page
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            return render_template('reset_password.html', error='Passwords do not match. Please try again.')
        
        # Update user's password in the database
        collection.update_one({'mobile_number': session['mobile_number']}, {'$set': {'password': new_password}})
        session.pop('otp')
        session.pop('mobile_number')
        return redirect(url_for('login'))

    return render_template('reset_password.html')

@app.route('/')
def index():
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        college_email = request.form['college_email']
        password = request.form['password']
        user_type = request.form['user_type']

        user = collection.find_one({'college_email': college_email, 'password': password, 'user_type': user_type})
        if user:
            session['college_email'] = college_email
            session['name'] = user.get('name', 'User')
            session['id'] = str(user.get('_id'))

            if user_type == 'teacher':
                return redirect(url_for('admin'))
            elif user_type == 'student':
                session['urn'] = user.get('URN')
                session['year'] = user.get('year')
                session['branch'] = user.get('branch')
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error='Invalid user type')

        else:
            return render_template('login.html', error='Invalid college email or password')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'college_email' in session:
        name = session.get('name', 'User')
        return render_template('dashboard.html', name=name)
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('college_email', None)
    session.pop('name', None)
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'college_email' in session:
        user = collection.find_one({'college_email': session['college_email']})
        if user:
            if request.method == 'POST':
                contact_number = request.form['contact_number']
                branch = request.form['branch']
                URN = request.form['URN']
                year = request.form['year']  # Extract the year from the form
                collection.update_one({'college_email': session['college_email']}, {'$set': {'contact_number': contact_number, 'branch': branch, 'URN': URN, 'year': year}})
                return redirect(url_for('profile'))
            return render_template('profile.html', user=user)
    return redirect(url_for('login'))

#Admin profile
@app.route('/admin_profile', methods=['GET', 'POST'])
def admin_profile():
    if 'college_email' in session:  # Assuming admin email is stored in session
        user = collection.find_one({'college_email': session['college_email']})
        if user:
            if request.method == 'POST':
                # Assuming you have fields like contact_number and branch for admins as well
                contact_number = request.form['contact_number']
                branch = request.form['branch']
                collection.update_one({'college_email': session['college_email']}, {'$set': {'contact_number': contact_number, 'branch': branch}})
                return redirect(url_for('admin_profile'))
            return render_template('admin_profile.html', user=user)
    return redirect(url_for('admin'))

@app.route('/assign_assignment', methods=['GET', 'POST'])
def assign_assignment():
    if request.method == 'POST':
        assignment_name = request.form.get('assignment_name')
        assignment = request.files.get('assignment')
        assignment_text = request.form.get('assignmentText')
        year = request.form.get('year')
        branch = request.form.get('branch')
        sections = request.form.getlist('sections[]')
        deadline = request.form.get('deadline')

        # Convert deadline string to datetime object
        deadline = datetime.datetime.strptime(deadline, '%Y-%m-%dT%H:%M')

        if assignment:
            # Secure the filename to prevent any unexpected behavior
            filename = secure_filename(assignment.filename)
            # Save the file to the upload folder
            assignment.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # Pass the filename to store_assignment function
            store_assignment(assignment_name, year, branch, sections, deadline, assignment=f"{app.config['UPLOAD_FOLDER']}//{filename}")
        elif assignment_text:
            with open('assignment.txt', 'w') as f:
                f.write(assignment_text)
            # Pass the assignment text to store_assignment function
            store_assignment(assignment_name, year, branch, sections, deadline, assignment_text=assignment_text)
        else:
            # Handle the case when neither assignment nor assignment_text is provided
            return "Error: No assignment provided", 400

        return redirect(url_for('admin'))  # Redirect to home page after successful submission
    else:
        return render_template('assign.html')

def store_assignment(name, year, branch, sections, deadline, assignment=None, assignment_text=None):
    # Generate a unique ID for the assignment
    assignment_id = str(uuid.uuid4())

    # Create a dictionary with the assignment details
    assignment_details = {
        'name': name,
        'assignment_id': assignment_id,
        'assignee_id': session['id'],
        'year': year,
        'branch': branch,
        'sections': sections,
        'deadline': deadline
    }

    # If an assignment file was uploaded, save it in the database
    if assignment:
        # Read the file content
        with open(assignment, "rb") as f:
            file_content = f.read()
        # Save the file content and content type separately
        assignment_details['assignment_file'] = Binary(file_content)
        assignment_details['content_type'] = mimetypes.guess_type(assignment)[0]
        os.remove(assignment)

    # If assignment text was provided, save it in the database
    if assignment_text:
        assignment_details['assignment_text'] = assignment_text

    # Insert the assignment details into the assignments collection
    assignments_collection.insert_one(assignment_details)

def retrieve_assignment_details(assignment_id):
    # Retrieve the assignment details from the database
    assignment_details = assignments_collection.find_one({'assignment_id': assignment_id})

    # If the assignment details include a file, save the file to disk
    if 'assignment_file' in assignment_details:
        # The assignment_file field is a bytes object
        file_content = assignment_details['assignment_file']
        # Retrieve the content type from the database
        content_type = assignment_details['content_type']
        # Generate a filename for the file
        filename = f"{assignment_id}.{content_type.split('/')[-1]}"
        # Save the file to disk
        with open(filename, "wb") as f:
            f.write(file_content)
    elif 'assignment_text' in assignment_details:
        file_content = assignment_details['assignment_text']
        with open(filename, "wb") as f:
            f.write(file_content)

def fetch_assignments():
    # Fetch assignments from the database
    assignments = assignments_collection.find()

    # Initialize a list to store assignment details
    assignment_list = []

    # Iterate over the fetched assignments
    for assignment in assignments:
        assignment_details = {
            'assignment_id': assignment.get('assignment_id'),
            'name': assignment.get('name'),  # Assuming you have a 'name' field for each assignment
            'description': assignment.get('description'),  # Assuming you have a 'description' field for each assignment
            'deadline': assignment.get('deadline').strftime('%Y-%m-%d %H:%M'),  # Convert deadline to string format
            # Add more assignment details as needed
        }
        assignment_list.append(assignment_details)

    return assignment_list

@app.route('/assignments', methods=['GET'])
def get_assignments():
    # Fetch assignments from the database using the fetch_assignments function
    assignments = fetch_assignments()

    # Render the HTML template with the fetched assignments
    return render_template('assignments.html', assignments=assignments)

app.jinja_env.filters['zip'] = zip

@app.route('/check_status', methods=['POST', 'GET'])
def check_status():
    if request.method == 'POST':
        assignment_id = request.form.get('assignment_id')
        collection = mongo.db[assignment_id]
        profile = mongo.db['profiles']

        cursor = list(collection.find({}))

        student_id = [item['student_id'] for item in cursor]

        # Query the database for students with matching year, branch, and user type
        profiles = list(profile.find({'year': "3", 'branch': 'ECE', 'user_type': 'student'}))

        # Prepare a list to store student information
        students = []

        # Iterate over the fetched student data
        for profile in profiles:
            student_info = {
                'id': profile.get('_id', ''),
                'URN': profile.get('URN', ''),  # Access URN from profile
                'Name': profile.get('name', ''),  # Access name from profile
            }
            students.append(student_info)

        submission_status = [
            'submitted' if str(student['id']) in [str(ObjectId(id)) for id in student_id] else 'not submitted'
            for student in students
        ]
        print("Status: ", submission_status)

            # Pass the status and other relevant data to the template
        return render_template('check_status.html', students=students, submission_status=submission_status)
    else:
        assignments = list(assignments_collection.find({}))

        assignment_list = [{'assignment_id': doc['assignment_id'], 'name': doc['name']} for doc in assignments]
        return render_template('check_status.html', assignment_list=assignment_list)
    # else:
    #     # Redirect if the user is not logged in
    #     return redirect(url_for('login'))



def custom_zip(*args):
    """Emulate the behavior of the zip function in Jinja2 templates."""
    # Find the shortest iterable
    min_length = min(len(arg) for arg in args)
    # Yield tuples of corresponding elements from each iterable
    for i in range(min_length):
        yield tuple(arg[i] for arg in args)

# Pass the custom_zip function to the Jinja2 environment
app.jinja_env.globals['custom_zip'] = custom_zip

#Developer Profile
@app.route('/developer')
def developer():
    return render_template('developer.html')

# Routes for list of students
@app.route('/list')
def students():
    return render_template('class_student.html')

@app.route('/submit_assignment1', methods=['GET', 'POST'])
def assignment():
    if request.method == 'POST':
        assignment = request.files.get('fileToUpload')
        assignment_id = request.form.get('assignment_id')

        collection = mongo.db[assignment_id]

        if assignment:
            # Secure the filename to prevent any unexpected behavior
            filename = secure_filename(assignment.filename)
            # Save the file content and content type separately
            content_type = mimetypes.guess_type(filename)[0]
            # Read the file content
            file_content = assignment.read()
            # Save the file to the upload folder
            assignment.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            data = {
                'assignment_id': assignment_id,
                'student_id': session['id'],
                'assignment_file': Binary(file_content),
                'content_type': content_type
            }

            collection.insert_one(data)

            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # Remove the file after saving to MongoDB

            # Return a JSON response to trigger the popup in the frontend
            return jsonify({'message': 'Assignment uploaded successfully'})

    cursor = list(assignments_collection.find({'year': session['year'], 'branch': session['branch']}))

    if not cursor:
        return jsonify({'error': 'No assignments found for the given user'})

    # Prepare a list of dictionaries, where each dictionary contains the assignment ID and its respective name
    assignment_list = [{'assignment_id': doc['assignment_id'], 'name': doc['name']} for doc in cursor]

    return render_template('upload.html', assignment_list=assignment_list)

# @app.route('/evaluate_assignments', methods=['POST'])
# def evaluate_assignments():
#     data = request.json
#     teacher_id = data.get('teacher_id')
    
#     # Fetch all assignments
#     all_assignments = assignments_collection.find()
    
#     # Evaluate each assignment for plagiarism and calculate scores
#     evaluation_results = []
#     for assignment in all_assignments:
#         plagiarism_percentage = detect_plagiarism(assignment['assignment_text'])
#         score = 10 - (plagiarism_percentage // 10)
#         evaluation_results.append({'student_id': assignment['student_id'], 'score': score})
    
#     return jsonify({'evaluation_results': evaluation_results})

# Download the punkt tokenizer once
# nltk.download('punkt')

import numpy as np

def check_plagiarism(raw_documents):
    # Tokenize the documents and keep track of line numbers
    tokenized_documents = []
    for doc_id, doc in enumerate(raw_documents):
        lines = sent_tokenize(doc)  # Split the document into lines
        tokenized_lines = [(line_id, word_tokenize(line)) for line_id, line in enumerate(lines, start=1)]
        tokenized_documents.append((doc_id, tokenized_lines))

    # Create the Dictionary and Corpus
    dictionary = Dictionary([tokens for doc_id, tokenized_lines in tokenized_documents for _, tokens in tokenized_lines])
    corpus = [dictionary.doc2bow(text) for doc_id, tokenized_lines in tokenized_documents for _, text in tokenized_lines]

    # Check plagiarism between all pairs of documents
    similarity_scores = []
    for i in range(len(raw_documents)):
        for j in range(i + 1, len(raw_documents)):
            vec1 = [dictionary.doc2bow(tokens) for _, tokens in tokenized_documents[i][1]]
            vec2 = [dictionary.doc2bow(tokens) for _, tokens in tokenized_documents[j][1]]
            vec1_flat = [item for sublist in vec1 for item in sublist]
            vec2_flat = [item for sublist in vec2 for item in sublist]
            vec1_sum = np.sum([corpus_vec[1] for corpus_vec in corpus if corpus_vec[0] in vec1_flat], axis=0)
            vec2_sum = np.sum([corpus_vec[1] for corpus_vec in corpus if corpus_vec[0] in vec2_flat], axis=0)
            sim = np.dot(vec1_sum, vec2_sum) / (np.linalg.norm(vec1_sum) * np.linalg.norm(vec2_sum))
            similarity_scores.append((i, j, sim))

    return similarity_scores


@app.route('/check_plagiarism')
def check_plagiarism_route():
    
    raw_documents = []
    folder_path = app.config['UPLOAD_FOLDER']

    # List all files in the folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Check if it's a file (not a folder) and has a '.txt' extension
        if os.path.isfile(file_path) and filename.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                raw_documents.append(content)

    similarity_scores = check_plagiarism(raw_documents)

    return jsonify({'similarity_scores': similarity_scores})

#route for fetching students
@app.route('/class_students', methods=['GET'])
def class_students():
    if 'college_email' in session:
        # Query the database for students with matching year, branch, and user type
        profiles = list(collection.find({'year': "3", 'branch': 'ECE', 'user_type': 'student'}))

        # Prepare a list to store student information
        students = []

        # Iterate over the fetched student data
        for profile in profiles:
            student_info = {
                'URN': profile.get('URN', ''),  # Access URN from profile
                'Name': profile.get('name', ''),  # Access name from profile
                'Contact Number': profile.get('contact_number', '')  # Access contact_number from profile
            }
            students.append(student_info)
        # Render the template with the student data
        return render_template('class_student.html', students=students)
    else:
        # Redirect if the user is not logged in
        return redirect(url_for('login'))



    
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text(data):
    text_values = []
    if isinstance(data, dict):
        for key, value in data.items():
            text_values.extend(extract_text(value))
    elif isinstance(data, list):
        for item in data:
            text_values.extend(extract_text(item))
    elif isinstance(data, str):
        words = data.replace('-', '\n').split()
        text_values.extend(words)
    return text_values

from flask import send_file
import os

@app.route('/ocr', methods=['GET', 'POST'])
def ocr():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('ocr.html', error='No file included in the request')

        file = request.files['file']
        if file.filename == '':
            return render_template('ocr.html', error='No file selected')

        if not allowed_file(file.filename):
            return render_template('ocr.html', error='File type not allowed')

        try:
            temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            file.save(temp_file_path)

            docs = DocumentFile.from_images(temp_file_path)
            model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)
            result = model(docs)
            json_output = result.export()
            extracted_text = extract_text(json_output)

            # Write the extracted text to a temporary text file
            text_file_path = 'extracted_text.txt'
            with open(text_file_path, 'w') as text_file:
                text_file.write('\n'.join(extracted_text))

            # Delete the temporary image file
            os.remove(temp_file_path)

            # Send the extracted text file as a download to the client
            return send_file(text_file_path, as_attachment=True, attachment_filename='extracted_text.txt')

        except Exception as e:
            return render_template('ocr.html', error=str(e))

    return render_template('ocr.html')

@app.route('/check_assignment_status', methods=['GET'])
def check_assignment_status():
    if 'college_email' in session:
        # Fetch the submitted assignments from the database
        submitted_assignments = list(answer_collection.find({'assignee_id': session['id']}))
        
        # Initialize a list to store assignment details
        assignment_details = []

        # Iterate over the submitted assignments
        for assignment in submitted_assignments:
            assignment_id = assignment.get('assignment_id')
            # Fetch assignment details
            assignment_info = assignments_collection.find_one({'assignment_id': assignment_id})
            if assignment_info:
                # Extract additional information about the student from their profile
                student_profile = collection.find_one({'_id': ObjectId(assignment.get('assignee_id'))})
                student_name = student_profile.get('name', '')
                student_urn = student_profile.get('URN', '')
                # Append assignment details along with student information to the list
                assignment_details.append({
                    'assignment_name': assignment_info.get('name', ''),
                    'student_name': student_name,
                    'student_urn': student_urn,
                    'submission_status': 'Submitted'  # You can add more status handling here if needed
                })
            else:
                assignment_details.append({
                    'assignment_name': 'Unknown',
                    'student_name': 'Unknown',
                    'student_urn': 'Unknown',
                    'submission_status': 'Submitted'
                })
        
        return render_template('assignment_status.html', assignment_details=assignment_details)
    else:
        # Redirect if the user is not logged in
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)

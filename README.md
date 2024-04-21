# Assign-FS

## Assignment Feedback System

This is a web application developed using Flask for managing student assignments, providing feedback, and facilitating communication between students and teachers.

## Features

- **User Authentication**: Users can sign up, log in, and reset their passwords.
- **Profile Management**: Users can update their contact information and branch details.
- **Assignment Submission**: Students can submit assignments through the system.
- **Plagiarism Detection**: Assignments are evaluated for plagiarism using a simple placeholder algorithm.
- **Feedback Mechanism**: Teachers can evaluate assignments and provide feedback to students.
- **Developer Profile**: A page showcasing the developer's information.

## Setup Instructions

To run the application locally, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/AdarshMishra26/Assign-FS.git
   ```

2. Install dependencies:
   ```bash
   cd Assign-FS
   pip install -r requirements.txt
   ```

3. Configure MongoDB:
   - Replace the MongoDB URI in `app.py` with your own URI.
   
4. Configure Flask-Mail:
   - Replace the SMTP server address, port, username, and password in `app.py` with your own credentials.

5. Run the application:
   ```bash
   python app.py
   ```

6. Access the application:
   Open a web browser and go to `http://localhost:5000` to access the application.

## Technology Stack

- **Python**: Programming language used for backend development.
- **Flask**: Web framework used for building the application.
- **MongoDB**: NoSQL database used for storing user profiles and assignments.
- **Flask-Mail**: Extension used for sending email notifications.
- **HTML/CSS**: Frontend development languages for creating user interfaces.
- **JavaScript**: Client-side scripting language for dynamic behavior.
- **Tailwind**: Frontend framework for responsive design.

## Contributors

- [Adarsh Mishra](https://github.com/AdarshMishra26)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

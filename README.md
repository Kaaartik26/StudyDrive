📂 StudyDrive – Simple File Sharing System (Flask, No Database)

A minimal Google-Drive–like web application designed for college labs and classrooms.
Students can upload and download files, while admins control folders and file management.

✔️ Flask backend
✔️ No database required
✔️ Files stored in server filesystem
✔️ JSON used for metadata
✔️ Role-based access (Admin & User)

🚀 Features
👤 User

view folders

view files inside folders

upload files

download files

cannot delete anything

cannot create folders

🔐 Admin

create folders

delete folders

upload files

delete any file

view everything

logout session

🛠 Tech Stack

Python Flask

HTML, CSS, JavaScript

JSON for metadata persistence

Server filesystem storage

🗂 How files are stored
uploads/
 ├── DSA/
 ├── DBMS/
 └── OS/


Metadata file:

file_meta.json


No SQL / No ORM / No external DB.

🧭 Use Cases

college programming labs

sharing lab solutions

internal file distribution

quick departmental file board

hackathons & mini-projects

▶️ How to run
pip install flask
python app.py


Then open:

http://127.0.0.1:5000/

🔑 Default Admin Password
admin123


Change it in app.py before real-world use.

🚧 Future Enhancements

file preview (PDF / code highlight)

drag-and-drop uploads

search inside folders

per-user upload limits

deployment guide (Railway / Render)

🏁 Why I built this

I wanted a simple classroom file-sharing system:

no Google sign-in

no database setup

works offline on local network

students can upload + download easily

So I built this using Flask & JSON ✨
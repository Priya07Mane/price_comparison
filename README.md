AI POWERED PRICE COMPARISON APPLICATION

A full-stack application that allows users to submit text or image inputs through a web interface and receive processed results from a Python backend.

The backend handles the core logic, while the frontend provides an interactive UI served using Live Server.

📌 FEATURES

🌐 Web-based interactive user interface

📝 Accepts text input from users

🖼️ Supports image upload for processing

🧠 Python-based backend for handling text and image processing

🔐 Uses environment variables (PROXY\_TOKEN) for secure API access

⚡ Displays results dynamically on the web page




TECH STACK

Frontend :

HTML

CSS

JavaScript

VS Code Live Server

Backend :

Python

Virtual Environment

External API (via PROXY\_TOKEN)




📂 PROJECT STRUCTURE

├── ai\_model.py

├── main.py

├── requirements.txt

├── index.html

├── env/

└── README.md




⚙️ INSTALLATION AND SETUP

1️⃣Extract the folder from the zip file and open in VSCode.

2️⃣ Create \& Activate Virtual Environment Windows- python -m venv venv ,then type- .\venv\Scripts\Activate

    macOS / Linux python3- -m venv env source env/bin/activate

3️⃣ Install Dependencies pip install -r requirements.txt

4️⃣ Set Environment Variable Windows (PowerShell) $env:PROXY_TOKEN="f1d8dd1d711149c5bdc00bf93504aad19430dbf5798"

    macOS / Linux export PROXY_TOKEN="f1d8dd1d711149c5bdc00bf93504aad19430dbf5798"

⚠️ Do not expose this token publicly in production environments.

5️⃣ Start the Backend Server python main.py

    Ensure the backend starts without errors and remains running.

6️⃣ Launch the Frontend

Open index.html in VS Code

Right-click inside the file

Select “Open with Live Server”

The web application will open in your browser.




🧪 HOW TO USE

Enter text or upload an image via the web interface

Submit the input

The backend processes the request

Results are displayed dynamically on the webpage




❗ IMPORTANT NOTES

Backend (main.py) must be running before using the web interface

Always activate the virtual environment before running the project

Designed for local development and testing




🐞 TROUBLESHOOTING

Upgrade pip if installation fails:

pip install --upgrade pip

Ensure Live Server extension is installed in VS Code

Check terminal logs if backend responses are not received



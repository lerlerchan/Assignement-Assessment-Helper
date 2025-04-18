# 📝 Assignment Assistant – PDF Upload App

This is a starter Flask web application that allows users to upload two PDF files:
- A **student assignment**
- A **grading rubric**

These files will later be processed using OCR and LLMs for automated grading and feedback.

---

## 🚀 Features

- Upload two PDF files via a simple web UI
- Validates file types (PDF only)
- Stores uploaded files in a local `uploads/` folder
- Ready for integration with PDF text extraction and AI processing

---

## 📁 Project Structure

assignment-assistant/
├── app.py # Flask backend
├── templates/
│ └── index.html # Upload UI
├── uploads/ # Stores uploaded PDFs (ignored by Git)
├── requirements.txt # Python dependencies
├── .gitignore # Excludes uploads, cache, env files
└── README.md # Project documentation


---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/assignment-assistant.git
cd assignment-assistant

---

### 2. Create a Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

#### 3. Install Dependencies
```bash
pip install -r requirements.txt

### 4. Run the App
```bash
python app.py

## Then open your browser and go to:
👉 http://localhost:5000

## 📦 Dependencies
Python 3.8+
Flask 2.x

## 🔒 Security Notes
Uploaded files are stored locally in uploads/ and are ignored by Git.
Make sure to sanitize and validate all user inputs in production environments.

## 📄 License
MIT License – feel free to use and modify.

## 🙋‍♂️ Author
Built by Ler-Kuan, Chan – [lkchan@sc.edu.my]
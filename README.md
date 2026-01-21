# Teacher Grading Assistant

A simple, AI-powered tool that helps teachers grade student assignments quickly and consistently. Upload your students' work, provide a rubric, and let AI do the grading while you review and approve the results.

## What This App Does

- **Saves Time**: Grade an entire class in minutes instead of hours
- **Consistent Grading**: AI applies the same standards to every student
- **Detailed Feedback**: Generates personalized comments for each student
- **Full Control**: Review and edit all grades before exporting
- **Easy Export**: Download grades as an Excel spreadsheet

---

## Features

- Upload student assignments (individual PDFs or one combined PDF)
- Provide your grading rubric (type it in or upload a PDF)
- AI grades assignments automatically based on your rubric
- Review all grades and make adjustments
- Export final grades to Excel, CSV, or JSON

---

## What You Need

### Required
- **Windows PC** (Windows 10 or 11)
- **Internet connection** (for cloud AI services)

### AI Service (Choose One)
You need access to at least one AI service:

| Service | Cost | Setup Difficulty |
|---------|------|------------------|
| **OpenAI (ChatGPT)** | Paid | Easy |
| **Anthropic (Claude)** | Paid | Easy |
| **Google Gemini** | Free tier available | Easy |
| **Ollama** | Free (runs on your PC) | Medium |
| **LM Studio** | Free (runs on your PC) | Medium |

**Recommended for beginners**: Start with Google Gemini (has a free tier) or OpenAI.

---

## Installation

### Option A: Run with Python (Recommended)

**Step 1: Download the Project**

1. Click the green "Code" button on GitHub
2. Select "Download ZIP"
3. Extract the ZIP file to a folder (e.g., `C:\TeacherGradingAssistant`)

**Step 2: Install Python**

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download Python 3.10 or newer
3. Run the installer
4. **Important**: Check the box "Add Python to PATH" during installation
5. Click "Install Now"

**Step 3: Install Required Packages**

1. Open Command Prompt (press Windows key, type `cmd`, press Enter)
2. Navigate to the project folder:
   ```
   cd C:\TeacherGradingAssistant
   ```
3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
4. Wait for installation to complete (this may take a few minutes)

**Step 4: Run the Application**

```
python app.py
```

The app will automatically open in your web browser at `http://localhost:5000`.

### Option B: Standalone EXE (Coming Soon)

A standalone executable that doesn't require Python installation will be available in future releases.

---

## First-Time Setup

Before you can grade assignments, you need to configure an AI provider.

### Setting Up Your AI Provider

1. Open the app in your browser
2. Click **Settings** (gear icon or menu)
3. Choose your AI provider from the dropdown
4. Enter your API key (see below for how to get one)
5. Click **Save Settings**
6. Click **Test Connection** to verify it works

### Getting API Keys

#### OpenAI (ChatGPT)
1. Go to [platform.openai.com](https://platform.openai.com/)
2. Create an account or sign in
3. Go to API Keys section
4. Click "Create new secret key"
5. Copy the key and paste it in the app settings

#### Anthropic (Claude)
1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Create an account or sign in
3. Go to API Keys
4. Create a new key
5. Copy and paste it in the app settings

#### Google Gemini (Free Tier Available)
1. Go to [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy and paste it in the app settings

#### Ollama (Free, Local)
1. Download Ollama from [ollama.ai](https://ollama.ai/)
2. Install and run Ollama
3. Open Command Prompt and run: `ollama pull llama2`
4. In the app settings, set the URL to `http://localhost:11434`
5. No API key needed

#### LM Studio (Free, Local)
1. Download LM Studio from [lmstudio.ai](https://lmstudio.ai/)
2. Download a model (e.g., Llama 2 or Mistral)
3. Start the local server in LM Studio
4. In the app settings, set the URL to `http://localhost:1234/v1`
5. No API key needed

---

## How to Grade Assignments

### Step 1: Upload Assignments

**For Individual PDF Files** (one PDF per student):
1. Select "Individual PDFs" option
2. Click "Choose Files" and select all student PDFs
3. File names will be used as student identifiers

**For Combined PDF** (all students in one file):
1. Select "Combined PDF" option
2. Upload your combined PDF
3. Choose how to split:
   - **By pages**: Specify how many pages per student
   - **By pattern**: If student IDs appear on pages, enter the pattern

### Step 2: Provide Your Rubric

**Type in your rubric**:
```
Content Understanding (40 points)
- Demonstrates clear understanding of topic: 20 points
- Uses relevant examples: 10 points
- Addresses all key questions: 10 points

Writing Quality (30 points)
- Clear organization: 15 points
- Grammar and spelling: 15 points

Critical Thinking (30 points)
- Original analysis: 15 points
- Logical arguments: 15 points
```

**Or upload a PDF** of your existing rubric.

### Step 3: Start Grading

1. Click **Start Grading**
2. Watch the progress bar as AI grades each assignment
3. Grading time depends on class size and AI provider

### Step 4: Review Results

After grading completes:
1. View all grades in a summary table
2. Click on any student to see detailed feedback
3. Edit grades or feedback as needed
4. All changes are saved automatically

### Step 5: Export Grades

1. Click **Export**
2. Choose format:
   - **Excel (.xlsx)** - Best for most use cases
   - **CSV** - For importing into other systems
   - **JSON** - For technical integrations
3. Download your grades file

---

## Tips for Best Results

### Writing Effective Rubrics

**Good rubric example**:
```
Introduction (20 points)
- Hook/attention grabber: 5 points
- Clear thesis statement: 10 points
- Preview of main points: 5 points
```

**Tips**:
- Be specific about what you're looking for
- Include point values for each criterion
- Break large categories into sub-criteria
- Use clear, measurable language

### PDF Format Tips

- Use clear, readable scans (300 DPI or higher)
- Avoid handwritten assignments if possible
- Ensure text is not too small or faded
- If using combined PDFs, ensure consistent page counts per student

### Grading Modes

- **Auto Mode**: AI assigns final grades directly
- **Suggestions Mode**: AI provides suggestions, you approve each grade

For first-time use, consider using Suggestions Mode to verify the AI understands your expectations.

---

## Troubleshooting

### "Connection Failed" Error

- Check your internet connection
- Verify your API key is correct
- Make sure the API key is active and has credits
- For local AI (Ollama/LM Studio), ensure the server is running

### "No Students Found" Error

- Check that your PDF files are readable
- Try uploading individual PDFs instead of combined
- Ensure PDFs aren't password-protected

### Grading is Very Slow

- Cloud AI services may have rate limits
- Try grading in smaller batches
- Consider using a local AI for large classes

### AI Grades Seem Wrong

- Review and improve your rubric specificity
- Try a different AI model
- Use Suggestions Mode to review each grade
- Remember: always review AI grades before final submission

### App Won't Start

1. Make sure Python is installed correctly:
   ```
   python --version
   ```
2. Reinstall requirements:
   ```
   pip install -r requirements.txt
   ```
3. Check for error messages in the command window

---

## Settings Explained

| Setting | Description |
|---------|-------------|
| **AI Provider** | Which AI service to use for grading |
| **Marking Mode** | Auto (direct grades) or Suggestions (review each) |
| **Feedback Style** | Brief or Detailed student feedback |
| **Default Total Marks** | Default maximum score (usually 100) |

---

## Privacy & Security

- **API keys** are encrypted and stored locally on your computer
- **Student data** is processed only during grading and not stored permanently
- **Uploaded files** are stored temporarily in the `uploads` folder
- Configuration is saved in your user folder (`~/.grading_assistant`)

---

## Getting Help

If you encounter issues:
1. Check the Troubleshooting section above
2. Review error messages in the command window
3. Open an issue on GitHub with details about your problem

---

## License

MIT License - Free to use and modify.

---

## Author

Built by Ler-Kuan, Chan - [lkchan@sc.edu.my]

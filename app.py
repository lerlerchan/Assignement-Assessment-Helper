"""
Teacher Grading Assistant - Main Application
A Flask-based web application for AI-powered assignment grading.
"""

import os
import sys
import asyncio
import threading
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, send_file, session
)
from werkzeug.utils import secure_filename

# Add the application directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import get_config
from utils.file_manager import FileManager
from services.pdf_service import PDFService
from services.ai_service import AIService
from services.grading_service import GradingService
from services.export_service import ExportService

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'grading-assistant-secret-key-change-in-production')

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

# Ensure upload folder exists
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

# Initialize services
file_manager = FileManager(UPLOAD_FOLDER)
pdf_service = PDFService()
ai_service = AIService()
grading_service = GradingService()
export_service = ExportService()

# Store active grading tasks (in production, use Redis or similar)
active_tasks = {}


def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def run_async(coro):
    """Run async function in a new event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ============================================================================
# Main Routes
# ============================================================================

@app.route('/')
def index():
    """Main upload page."""
    config = get_config()
    providers = ai_service.get_available_providers()

    return render_template('index.html',
                           providers=providers,
                           current_provider=config.get('ai_provider', 'openai'),
                           marking_mode=config.get('marking_mode', 'auto'),
                           feedback_style=config.get('feedback_style', 'detailed'))


@app.route('/upload', methods=['POST'])
def upload():
    """Handle file upload and start grading process."""
    try:
        config = get_config()

        # Update config from form
        if request.form.get('ai_provider'):
            config.set('ai_provider', request.form.get('ai_provider'))
        if request.form.get('marking_mode'):
            config.set('marking_mode', request.form.get('marking_mode'))
        if request.form.get('feedback_style'):
            config.set('feedback_style', request.form.get('feedback_style'))

        # Create grading session
        grading_session = grading_service.create_session()
        session['grading_session_id'] = grading_session.id

        # Handle assignment upload
        upload_type = request.form.get('upload_type', 'individual')
        pdf_paths = []

        if upload_type == 'individual':
            files = request.files.getlist('assignments')
            if not files or all(f.filename == '' for f in files):
                flash('Please upload at least one assignment PDF.', 'error')
                return redirect(url_for('index'))

            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    saved_path, _ = file_manager.save_uploaded_file(file, 'assignments')
                    pdf_paths.append(saved_path)

            # Load students from individual PDFs
            grading_service.load_students_from_pdfs(
                grading_session.id,
                pdf_paths,
                is_combined=False
            )

        else:  # combined PDF
            combined_file = request.files.get('combined_pdf')
            if not combined_file or combined_file.filename == '':
                flash('Please upload a combined PDF.', 'error')
                return redirect(url_for('index'))

            if not allowed_file(combined_file.filename):
                flash('Invalid file type. Please upload a PDF.', 'error')
                return redirect(url_for('index'))

            saved_path, _ = file_manager.save_uploaded_file(combined_file, 'assignments')
            pdf_paths.append(saved_path)

            # Get split parameters
            split_method = request.form.get('split_method', 'pages')
            pages_per_student = None
            student_id_pattern = None

            if split_method == 'pages':
                pages_per_student = int(request.form.get('pages_per_student', 1))
            else:
                student_id_pattern = request.form.get('student_id_pattern')

            grading_service.load_students_from_pdfs(
                grading_session.id,
                pdf_paths,
                is_combined=True,
                pages_per_student=pages_per_student,
                student_id_pattern=student_id_pattern
            )

        # Handle rubric
        rubric_type = request.form.get('rubric_type', 'text')

        if rubric_type == 'text':
            rubric_text = request.form.get('rubric_text', '').strip()
            if not rubric_text:
                flash('Please provide a rubric.', 'error')
                return redirect(url_for('index'))
            grading_service.load_rubric(grading_session.id, rubric_text, 'text')
        else:
            rubric_file = request.files.get('rubric_pdf')
            if not rubric_file or rubric_file.filename == '':
                flash('Please upload a rubric PDF.', 'error')
                return redirect(url_for('index'))

            if not allowed_file(rubric_file.filename):
                flash('Invalid rubric file type. Please upload a PDF.', 'error')
                return redirect(url_for('index'))

            saved_path, _ = file_manager.save_uploaded_file(rubric_file, 'rubrics')
            grading_service.load_rubric(grading_session.id, saved_path, 'pdf')

        # Check if we have students loaded
        grading_session = grading_service.get_session(grading_session.id)
        if not grading_session.students:
            flash('Could not extract any students from the uploaded files.', 'error')
            return redirect(url_for('index'))

        # Redirect to progress page
        return redirect(url_for('progress', session_id=grading_session.id))

    except Exception as e:
        flash(f'Error processing files: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/progress/<session_id>')
def progress(session_id):
    """Show grading progress page."""
    grading_session = grading_service.get_session(session_id)
    if not grading_session:
        flash('Session not found.', 'error')
        return redirect(url_for('index'))

    return render_template('progress.html',
                           session_id=session_id,
                           total_students=len(grading_session.students))


@app.route('/review/<session_id>')
def review(session_id):
    """Show grade review and editing page."""
    grading_session = grading_service.get_session(session_id)
    if not grading_session:
        flash('Session not found.', 'error')
        return redirect(url_for('index'))

    # Calculate statistics
    results = grading_session.results
    if results:
        percentages = [r.percentage for r in results]
        avg_percentage = sum(percentages) / len(percentages)
        max_percentage = max(percentages)
        min_percentage = min(percentages)
    else:
        avg_percentage = max_percentage = min_percentage = 0

    return render_template('review.html',
                           session_id=session_id,
                           results=results,
                           avg_percentage=avg_percentage,
                           max_percentage=max_percentage,
                           min_percentage=min_percentage)


@app.route('/export/<session_id>')
def export(session_id):
    """Export grades to file."""
    grading_session = grading_service.get_session(session_id)
    if not grading_session:
        flash('Session not found.', 'error')
        return redirect(url_for('index'))

    export_format = request.args.get('format', 'excel')

    try:
        if export_format == 'excel':
            filepath = file_manager.get_export_path('grades.xlsx')
            export_service.export_to_excel(grading_session, filepath)
            return send_file(filepath, as_attachment=True, download_name='grades.xlsx')
        elif export_format == 'csv':
            filepath = file_manager.get_export_path('grades.csv')
            export_service.export_to_csv(grading_session, filepath)
            return send_file(filepath, as_attachment=True, download_name='grades.csv')
        elif export_format == 'json':
            filepath = file_manager.get_export_path('grades.json')
            export_service.export_to_json(grading_session, filepath)
            return send_file(filepath, as_attachment=True, download_name='grades.json')
        else:
            flash('Invalid export format.', 'error')
            return redirect(url_for('review', session_id=session_id))
    except Exception as e:
        flash(f'Export error: {str(e)}', 'error')
        return redirect(url_for('review', session_id=session_id))


# ============================================================================
# Configuration Routes
# ============================================================================

@app.route('/config')
def config():
    """Settings page."""
    config_manager = get_config()
    return render_template('config.html', config=config_manager.get_all())


@app.route('/config/save', methods=['POST'])
def save_config():
    """Save configuration settings."""
    config_manager = get_config()

    # Collect form data
    updates = {}
    fields = [
        'ai_provider', 'openai_api_key', 'anthropic_api_key', 'gemini_api_key',
        'ollama_url', 'ollama_model', 'lmstudio_url', 'lmstudio_model',
        'generic_url', 'generic_api_key', 'generic_model',
        'marking_mode', 'feedback_style', 'default_total_marks'
    ]

    for field in fields:
        value = request.form.get(field)
        if value is not None:
            # Don't update masked API keys
            if 'api_key' in field and value.startswith('***'):
                continue
            updates[field] = value

    config_manager.update(updates)
    flash('Settings saved successfully.', 'success')
    return redirect(url_for('config'))


@app.route('/config/reset')
def reset_config():
    """Reset configuration to defaults."""
    config_manager = get_config()
    config_manager.reset()
    flash('Settings reset to defaults.', 'success')
    return redirect(url_for('config'))


# ============================================================================
# API Routes
# ============================================================================

@app.route('/api/test-provider', methods=['POST'])
def api_test_provider():
    """Test AI provider connection."""
    data = request.get_json()
    provider = data.get('provider', 'openai')

    result = run_async(ai_service.test_provider(provider))
    return jsonify(result)


@app.route('/api/start-grading/<session_id>', methods=['POST'])
def api_start_grading(session_id):
    """Start the grading process in background."""
    grading_session = grading_service.get_session(session_id)
    if not grading_session:
        return jsonify({'success': False, 'message': 'Session not found'})

    if session_id in active_tasks:
        return jsonify({'success': False, 'message': 'Grading already in progress'})

    def grade_task():
        try:
            run_async(grading_service.grade_all(session_id))
        except Exception as e:
            grading_session = grading_service.get_session(session_id)
            if grading_session:
                grading_session.status = 'error'
                grading_session.error_message = str(e)
        finally:
            if session_id in active_tasks:
                del active_tasks[session_id]

    thread = threading.Thread(target=grade_task)
    thread.start()
    active_tasks[session_id] = thread

    return jsonify({'success': True, 'message': 'Grading started'})


@app.route('/api/progress/<session_id>')
def api_progress(session_id):
    """Get grading progress."""
    progress = grading_service.get_progress(session_id)
    if 'error' in progress:
        return jsonify(progress), 404
    return jsonify(progress)


@app.route('/api/cancel/<session_id>', methods=['POST'])
def api_cancel(session_id):
    """Cancel grading process."""
    grading_service.delete_session(session_id)
    if session_id in active_tasks:
        del active_tasks[session_id]
    return jsonify({'success': True})


@app.route('/api/update-grade', methods=['POST'])
def api_update_grade():
    """Update a student's grade."""
    data = request.get_json()
    session_id = data.get('session_id')
    student_id = data.get('student_id')
    element_name = data.get('element_name')
    marks = data.get('marks')
    feedback = data.get('feedback')
    overall_feedback = data.get('overall_feedback')

    success = grading_service.update_grade(
        session_id,
        student_id,
        element_name=element_name,
        marks=marks if marks is not None else None,
        overall_feedback=overall_feedback
    )

    return jsonify({'success': success})


@app.route('/api/providers')
def api_providers():
    """Get available AI providers."""
    providers = ai_service.get_available_providers()
    return jsonify(providers)


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found_error(error):
    flash('Page not found.', 'error')
    return redirect(url_for('index'))


@app.errorhandler(500)
def internal_error(error):
    flash('An internal error occurred. Please try again.', 'error')
    return redirect(url_for('index'))


@app.errorhandler(413)
def file_too_large(error):
    flash('File too large. Maximum size is 50MB.', 'error')
    return redirect(url_for('index'))


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run the application."""
    import webbrowser
    from threading import Timer

    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'

    # Open browser after a short delay
    if not debug:
        def open_browser():
            webbrowser.open(f'http://localhost:{port}')
        Timer(1.5, open_browser).start()

    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    main()

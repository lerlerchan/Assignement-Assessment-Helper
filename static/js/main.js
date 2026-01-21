// Main JavaScript file for Teacher Grading Assistant

document.addEventListener('DOMContentLoaded', function() {
    initializeFileDropZones();
    initializeFormValidation();
});

// File Drop Zone Functionality
function initializeFileDropZones() {
    const dropZones = document.querySelectorAll('.file-upload');

    dropZones.forEach(zone => {
        const input = zone.querySelector('input[type="file"]');

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            zone.addEventListener(eventName, preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            zone.addEventListener(eventName, () => zone.classList.add('drag-over'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            zone.addEventListener(eventName, () => zone.classList.remove('drag-over'), false);
        });

        zone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (input && files.length > 0) {
                // For file inputs that accept multiple files
                if (input.multiple) {
                    input.files = files;
                } else {
                    // Create a new DataTransfer to set single file
                    const dt = new DataTransfer();
                    dt.items.add(files[0]);
                    input.files = dt.files;
                }
                // Trigger change event
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
    });
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Form Validation
function initializeFormValidation() {
    const uploadForm = document.getElementById('upload-form');

    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            const uploadType = document.querySelector('input[name="upload_type"]:checked').value;
            const rubricType = document.querySelector('input[name="rubric_type"]:checked').value;

            // Validate assignment files
            if (uploadType === 'individual') {
                const files = document.getElementById('assignments').files;
                if (files.length === 0) {
                    e.preventDefault();
                    showError('Please upload at least one assignment PDF.');
                    return;
                }
            } else {
                const combinedPdf = document.getElementById('combined_pdf').files;
                if (combinedPdf.length === 0) {
                    e.preventDefault();
                    showError('Please upload the combined PDF file.');
                    return;
                }
            }

            // Validate rubric
            if (rubricType === 'text') {
                const rubricText = document.getElementById('rubric_text').value.trim();
                if (rubricText.length < 10) {
                    e.preventDefault();
                    showError('Please enter a rubric (at least 10 characters).');
                    return;
                }
            } else {
                const rubricPdf = document.getElementById('rubric_pdf').files;
                if (rubricPdf.length === 0) {
                    e.preventDefault();
                    showError('Please upload the rubric PDF file.');
                    return;
                }
            }

            // Show loading state
            const submitBtn = uploadForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Processing...';
        });
    }
}

function showError(message) {
    // Create flash message
    const flashContainer = document.querySelector('.flash-messages') || createFlashContainer();
    const flash = document.createElement('div');
    flash.className = 'flash flash-error';
    flash.innerHTML = `
        ${message}
        <button class="flash-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    flashContainer.appendChild(flash);

    // Auto-remove after 5 seconds
    setTimeout(() => flash.remove(), 5000);
}

function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-messages';
    const mainContent = document.querySelector('.container');
    mainContent.insertBefore(container, mainContent.firstChild.nextSibling);
    return container;
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// API Helper Functions
async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Progress Polling
class ProgressPoller {
    constructor(sessionId, updateCallback, completeCallback) {
        this.sessionId = sessionId;
        this.updateCallback = updateCallback;
        this.completeCallback = completeCallback;
        this.interval = null;
    }

    start() {
        this.poll();
        this.interval = setInterval(() => this.poll(), 1000);
    }

    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }

    async poll() {
        try {
            const data = await apiCall(`/api/progress/${this.sessionId}`);
            this.updateCallback(data);

            if (data.status === 'completed' || data.status === 'error') {
                this.stop();
                this.completeCallback(data);
            }
        } catch (error) {
            console.error('Progress poll failed:', error);
        }
    }
}

// Export for global use
window.formatFileSize = formatFileSize;
window.apiCall = apiCall;
window.ProgressPoller = ProgressPoller;

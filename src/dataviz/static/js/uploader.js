/**
 * DataViz — File Upload & Paste Handler
 * Handles drag-and-drop file uploads and text paste submissions.
 */

document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const pasteArea = document.getElementById('paste-area');
    const parseBtn = document.getElementById('btn-parse-paste');
    const hasHeaderCheck = document.getElementById('has-header-check');

    // --- Drop zone events ---
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            uploadFile(files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            uploadFile(fileInput.files[0]);
        }
    });

    // --- Paste button ---
    parseBtn.addEventListener('click', () => {
        const text = pasteArea.value.trim();
        if (!text) {
            App.showToast('Please paste some data first', 'error');
            return;
        }
        pasteData(text);
    });

    /**
     * Upload a file to the API.
     */
    function uploadFile(file) {
        // Validate extension
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        const allowed = ['.csv', '.tsv', '.txt'];
        if (!allowed.includes(ext)) {
            App.showToast(`File type "${ext}" not supported. Use CSV, TSV, or TXT.`, 'error');
            return;
        }

        // Validate size (50MB default)
        if (file.size > 50 * 1024 * 1024) {
            App.showToast('File is too large. Maximum size is 50MB.', 'error');
            return;
        }

        App.showLoading(true);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('has_header', hasHeaderCheck.checked ? 'true' : 'false');

        fetch('/api/upload', {
            method: 'POST',
            body: formData,
        })
            .then(res => {
                if (!res.ok) return res.json().then(data => { throw new Error(data.detail || 'Upload failed'); });
                return res.json();
            })
            .then(data => {
                App.showLoading(false);
                App.handleDataResponse(data);
            })
            .catch(err => {
                App.showLoading(false);
                App.showToast(err.message, 'error');
            });
    }

    /**
     * Parse pasted text data.
     */
    function pasteData(text) {
        App.showLoading(true);

        const formData = new FormData();
        formData.append('text', text);
        formData.append('has_header', hasHeaderCheck.checked ? 'true' : 'false');

        fetch('/api/paste', {
            method: 'POST',
            body: formData,
        })
            .then(res => {
                if (!res.ok) return res.json().then(data => { throw new Error(data.detail || 'Parse failed'); });
                return res.json();
            })
            .then(data => {
                App.showLoading(false);
                App.handleDataResponse(data);
            })
            .catch(err => {
                App.showLoading(false);
                App.showToast(err.message, 'error');
            });
    }
});

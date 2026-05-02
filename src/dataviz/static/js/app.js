/**
 * DataViz — Main Application Controller
 * Coordinates upload → parse → chart flow and manages application state.
 */

const App = (() => {
    // Application state
    const state = {
        sessionId: null,
        profile: null,
        recommendations: [],
        currentChart: null,
    };

    /**
     * Show a toast notification.
     */
    function showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100px)';
            toast.style.transition = '0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    /**
     * Show loading overlay.
     */
    function showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        overlay.style.display = show ? 'flex' : 'none';
    }

    /**
     * Handle successful data parsing response.
     */
    function handleDataResponse(data) {
        state.sessionId = data.session_id;
        state.profile = data.profile;
        state.recommendations = data.recommendations;

        // Show data preview
        renderDataPreview(data.profile);

        // Show chart gallery
        ChartModule.renderGallery(data.recommendations);

        showToast(`Loaded ${data.profile.row_count} rows × ${data.profile.columns.length} columns`, 'success');
    }

    /**
     * Render the data preview table.
     */
    function renderDataPreview(profile) {
        const section = document.getElementById('data-preview-section');
        const thead = document.getElementById('data-table-head');
        const tbody = document.getElementById('data-table-body');
        const info = document.getElementById('data-info');

        section.style.display = 'block';
        section.classList.add('fade-in');

        info.textContent = `${profile.row_count} rows × ${profile.columns.length} columns`;

        // Header row with type badges
        let headerHtml = '<tr>';
        profile.columns.forEach(col => {
            const badgeClass = `col-type-${col.dtype}`;
            headerHtml += `<th>${escapeHtml(col.name)}<span class="col-type-badge ${badgeClass}">${col.dtype}</span></th>`;
        });
        headerHtml += '</tr>';
        thead.innerHTML = headerHtml;

        // Data rows
        let bodyHtml = '';
        const rows = profile.preview_rows.slice(0, 50);
        rows.forEach(row => {
            bodyHtml += '<tr>';
            profile.columns.forEach(col => {
                const val = row[col.name];
                bodyHtml += `<td>${val !== null && val !== undefined ? escapeHtml(String(val)) : '<span style="color:var(--text-muted)">null</span>'}</td>`;
            });
            bodyHtml += '</tr>';
        });
        tbody.innerHTML = bodyHtml;

        // Populate controls
        Controls.populateColumns(profile.columns);
    }

    /**
     * Escape HTML entities.
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Public API
    return {
        state,
        showToast,
        showLoading,
        handleDataResponse,
        renderDataPreview,
        escapeHtml,
    };
})();

// --- Tab switching ---
document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(btn => {
        btn.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.add('active');
        });
    });

    // Load sample data list
    fetch('/api/sample-data')
        .then(res => res.json())
        .then(samples => {
            const grid = document.getElementById('sample-grid');
            samples.forEach(s => {
                const card = document.createElement('div');
                card.className = 'sample-card';
                card.innerHTML = `
                    <div class="sample-card-title">${App.escapeHtml(s.name)}</div>
                    <div class="sample-card-desc">${App.escapeHtml(s.description)}</div>
                `;
                card.addEventListener('click', () => {
                    App.showLoading(true);
                    fetch(`/api/sample-data/${s.id}`, { method: 'POST' })
                        .then(res => res.json())
                        .then(data => {
                            App.showLoading(false);
                            App.handleDataResponse(data);
                        })
                        .catch(err => {
                            App.showLoading(false);
                            App.showToast('Failed to load sample data: ' + err.message, 'error');
                        });
                });
                grid.appendChild(card);
            });
        })
        .catch(() => {});
});

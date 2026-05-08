/**
 * DataViz — Chart Template Manager
 * Saves and restores chart configurations via localStorage.
 */

const TemplateManager = (() => {
    const STORAGE_KEY = 'dataviz_templates';

    /**
     * Load all templates from localStorage.
     */
    function _loadAll() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            return raw ? JSON.parse(raw) : [];
        } catch {
            return [];
        }
    }

    /**
     * Persist templates to localStorage.
     */
    function _saveAll(templates) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(templates));
    }

    /**
     * Get all saved templates.
     */
    function list() {
        return _loadAll();
    }

    /**
     * Save current chart controls as a named template.
     */
    function save(name) {
        if (!name || !name.trim()) return false;

        const values = Controls.getControlValues();
        if (!values) return false;

        const template = {
            name: name.trim(),
            ...values,
            created_at: new Date().toISOString(),
        };

        const templates = _loadAll();
        // Replace existing template with same name
        const idx = templates.findIndex(t => t.name === template.name);
        if (idx >= 0) {
            templates[idx] = template;
        } else {
            templates.push(template);
        }

        _saveAll(templates);
        return true;
    }

    /**
     * Apply a saved template to the control panel and trigger chart update.
     */
    function apply(template) {
        if (!App.state.sessionId) {
            App.showToast('No data loaded. Please upload data first.', 'error');
            return;
        }

        // Check if columns exist in current data
        const currentCols = App.state.profile
            ? App.state.profile.columns.map(c => c.name)
            : [];

        const missingCols = [];
        if (template.x_column && !currentCols.includes(template.x_column)) {
            missingCols.push(template.x_column);
        }
        if (template.y_column && !currentCols.includes(template.y_column)) {
            missingCols.push(template.y_column);
        }
        if (template.columns && template.columns.length > 0) {
            template.columns.forEach(c => {
                if (!currentCols.includes(c) && !missingCols.includes(c)) {
                    missingCols.push(c);
                }
            });
        }

        if (missingCols.length > 0) {
            App.showToast(
                `Warning: columns not found in data: ${missingCols.join(', ')}. Template may not render correctly.`,
                'error'
            );
        }

        // Apply values to controls
        Controls.applyTemplate(template);

        // Show workspace if in gallery view
        const gallery = document.getElementById('chart-gallery-section');
        const workspace = document.getElementById('chart-workspace-section');
        if (gallery.style.display !== 'none') {
            gallery.style.display = 'none';
            workspace.style.display = 'block';
            workspace.classList.add('fade-in');
        }

        // Trigger chart update
        Controls.updateChart();
        App.showToast(`Template "${template.name}" applied`, 'success');
    }

    /**
     * Remove a template by name.
     */
    function remove(name) {
        const templates = _loadAll().filter(t => t.name !== name);
        _saveAll(templates);
    }

    /**
     * Render the template list in the sidebar panel.
     */
    function renderList() {
        const container = document.getElementById('template-list');
        const emptyMsg = document.getElementById('template-empty');
        const templates = _loadAll();

        // Clear existing items (keep empty message)
        container.querySelectorAll('.template-item').forEach(el => el.remove());

        if (templates.length === 0) {
            emptyMsg.style.display = 'block';
            return;
        }

        emptyMsg.style.display = 'none';

        templates.forEach(tmpl => {
            const item = document.createElement('div');
            item.className = 'template-item';
            item.innerHTML = `
                <div class="template-item-info">
                    <span class="template-item-name">${App.escapeHtml(tmpl.name)}</span>
                    <span class="template-item-type">${tmpl.chart_type}</span>
                </div>
                <div class="template-item-actions">
                    <button class="btn-icon btn-apply-tmpl" title="Apply template">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                    </button>
                    <button class="btn-icon btn-delete-tmpl" title="Delete template">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                    </button>
                </div>
            `;

            item.querySelector('.btn-apply-tmpl').addEventListener('click', (e) => {
                e.stopPropagation();
                apply(tmpl);
            });

            item.querySelector('.btn-delete-tmpl').addEventListener('click', (e) => {
                e.stopPropagation();
                remove(tmpl.name);
                renderList();
                App.showToast(`Template "${tmpl.name}" deleted`, 'success');
            });

            container.appendChild(item);
        });
    }

    /**
     * Prompt user for template name and save.
     */
    function promptSave() {
        const name = prompt('Enter a name for this template:');
        if (!name) return;

        if (save(name)) {
            renderList();
            App.showToast(`Template "${name.trim()}" saved`, 'success');
        } else {
            App.showToast('Failed to save template. Make sure a chart is configured.', 'error');
        }
    }

    return {
        list,
        save,
        apply,
        remove,
        renderList,
        promptSave,
    };
})();

// --- Event bindings ---
document.addEventListener('DOMContentLoaded', () => {
    // Save template button
    document.getElementById('btn-save-template').addEventListener('click', TemplateManager.promptSave);

    // Render initial template list
    TemplateManager.renderList();
});

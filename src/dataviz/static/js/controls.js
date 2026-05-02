/**
 * DataViz — Chart Control Panel
 * Manages column selectors, chart type switching, and real-time chart updates.
 */

const Controls = (() => {
    /**
     * Populate column dropdowns from data profile.
     */
    function populateColumns(columns) {
        const xSelect = document.getElementById('ctrl-x-column');
        const ySelect = document.getElementById('ctrl-y-column');
        const multiCols = document.getElementById('ctrl-multi-cols');

        // Clear existing
        xSelect.innerHTML = '<option value="">— Select —</option>';
        ySelect.innerHTML = '<option value="">— Select —</option>';
        multiCols.innerHTML = '';

        columns.forEach(col => {
            const optX = document.createElement('option');
            optX.value = col.name;
            optX.textContent = `${col.name} (${col.dtype})`;
            xSelect.appendChild(optX);

            const optY = optX.cloneNode(true);
            ySelect.appendChild(optY);

            // Multi-column checkboxes
            const label = document.createElement('label');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = col.name;
            checkbox.checked = col.dtype === 'numeric';
            label.appendChild(checkbox);
            label.appendChild(document.createTextNode(` ${col.name}`));
            multiCols.appendChild(label);
        });
    }

    /**
     * Set control values from a chart recommendation.
     */
    function setFromRecommendation(rec) {
        const typeSelect = document.getElementById('ctrl-chart-type');
        const xSelect = document.getElementById('ctrl-x-column');
        const ySelect = document.getElementById('ctrl-y-column');
        const titleInput = document.getElementById('ctrl-title');

        typeSelect.value = rec.chart_type;
        titleInput.value = rec.title || '';

        if (rec.x_column) xSelect.value = rec.x_column;
        if (rec.y_column) ySelect.value = rec.y_column;

        // Show/hide multi-column group for heatmap/grouped bar
        const multiGroup = document.getElementById('ctrl-multi-cols-group');
        const needsMulti = ['heatmap', 'grouped_bar', 'stacked_bar'].includes(rec.chart_type);
        multiGroup.style.display = needsMulti ? 'flex' : 'none';

        if (needsMulti && rec.columns.length > 0) {
            const checkboxes = document.querySelectorAll('#ctrl-multi-cols input[type="checkbox"]');
            checkboxes.forEach(cb => {
                cb.checked = rec.columns.includes(cb.value);
            });
        }

        updateVisibility(rec.chart_type);
    }

    /**
     * Show/hide X/Y selectors based on chart type needs.
     */
    function updateVisibility(chartType) {
        const xGroup = document.getElementById('ctrl-x-group');
        const yGroup = document.getElementById('ctrl-y-group');
        const multiGroup = document.getElementById('ctrl-multi-cols-group');

        const needsMulti = ['heatmap', 'grouped_bar', 'stacked_bar'].includes(chartType);
        const needsX = !['box'].includes(chartType);
        const needsY = !['histogram', 'pie'].includes(chartType) || !needsMulti;

        xGroup.style.display = needsX ? 'flex' : 'none';
        yGroup.style.display = needsY && !needsMulti ? 'flex' : 'none';
        multiGroup.style.display = needsMulti ? 'flex' : 'none';
    }

    /**
     * Collect current control values and send chart request to API.
     */
    function updateChart() {
        const sessionId = App.state.sessionId;
        if (!sessionId) {
            App.showToast('No data loaded. Please upload data first.', 'error');
            return;
        }

        const chartType = document.getElementById('ctrl-chart-type').value;
        const xColumn = document.getElementById('ctrl-x-column').value;
        const yColumn = document.getElementById('ctrl-y-column').value;
        const title = document.getElementById('ctrl-title').value;
        const xLabel = document.getElementById('ctrl-x-label').value;
        const yLabel = document.getElementById('ctrl-y-label').value;
        const aggregation = document.getElementById('ctrl-aggregation').value;
        const colorScheme = document.getElementById('ctrl-color').value;

        // Collect multi-columns if needed
        const multiCols = [];
        document.querySelectorAll('#ctrl-multi-cols input:checked').forEach(cb => {
            multiCols.push(cb.value);
        });

        const formData = new FormData();
        formData.append('session_id', sessionId);
        formData.append('chart_type', chartType);
        if (xColumn) formData.append('x_column', xColumn);
        if (yColumn) formData.append('y_column', yColumn);
        if (title) formData.append('title', title);
        if (xLabel) formData.append('x_label', xLabel);
        if (yLabel) formData.append('y_label', yLabel);
        if (aggregation) formData.append('aggregation', aggregation);
        if (colorScheme) formData.append('color_scheme', colorScheme);
        if (multiCols.length > 0) formData.append('columns', multiCols.join(','));

        fetch('/api/chart', {
            method: 'POST',
            body: formData,
        })
            .then(res => {
                if (!res.ok) return res.json().then(data => { throw new Error(data.detail || 'Chart generation failed'); });
                return res.json();
            })
            .then(data => {
                ChartModule.renderMainChart(data.plotly_data, data.plotly_layout);
                App.showToast('Chart updated!', 'success');
            })
            .catch(err => {
                App.showToast(err.message, 'error');
            });
    }

    return {
        populateColumns,
        setFromRecommendation,
        updateChart,
        updateVisibility,
    };
})();

// --- Event bindings ---
document.addEventListener('DOMContentLoaded', () => {
    // Update chart button
    document.getElementById('btn-update-chart').addEventListener('click', Controls.updateChart);

    // Export PNG
    document.getElementById('btn-export-png').addEventListener('click', ChartModule.exportPng);

    // Back to gallery
    document.getElementById('btn-back-gallery').addEventListener('click', () => {
        document.getElementById('chart-workspace-section').style.display = 'none';
        document.getElementById('chart-gallery-section').style.display = 'block';
    });

    // Chart type change — update visibility
    document.getElementById('ctrl-chart-type').addEventListener('change', (e) => {
        Controls.updateVisibility(e.target.value);
    });
});

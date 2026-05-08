/**
 * DataViz — Chart Control Panel
 * Manages column selectors, chart type switching, and real-time chart updates.
 * Supports multi-Y axis selection for line, scatter, area, and bar charts.
 */

const Controls = (() => {
    /**
     * Populate column dropdowns and multi-Y checkboxes from data profile.
     */
    function populateColumns(columns) {
        const xSelect = document.getElementById('ctrl-x-column');
        const ySelect = document.getElementById('ctrl-y-column');
        const multiY = document.getElementById('ctrl-y-multi');
        const multiCols = document.getElementById('ctrl-multi-cols');

        // Clear existing
        xSelect.innerHTML = '<option value="">— Select —</option>';
        ySelect.innerHTML = '<option value="">— Select —</option>';
        multiY.innerHTML = '';
        multiCols.innerHTML = '';

        columns.forEach(col => {
            const optX = document.createElement('option');
            optX.value = col.name;
            optX.textContent = `${col.name} (${col.dtype})`;
            xSelect.appendChild(optX);

            const optY = optX.cloneNode(true);
            ySelect.appendChild(optY);

            // Multi-Y checkboxes (for multi-series line/scatter/area)
            const yLabel = document.createElement('label');
            const yCb = document.createElement('input');
            yCb.type = 'checkbox';
            yCb.value = col.name;
            yCb.dataset.dtype = col.dtype;
            yLabel.appendChild(yCb);
            yLabel.appendChild(document.createTextNode(` ${col.name}`));
            if (col.dtype !== 'numeric') {
                yLabel.style.opacity = '0.5';
            }
            multiY.appendChild(yLabel);

            // Multi-column checkboxes (for heatmap/grouped bar)
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

        // Reset multi-Y checkboxes
        const multiYCbs = document.querySelectorAll('#ctrl-y-multi input[type="checkbox"]');
        multiYCbs.forEach(cb => {
            cb.checked = false;
        });

        // For multi-column chart types (heatmap, grouped_bar, stacked_bar), set multi-cols
        const multiColsCbs = document.querySelectorAll('#ctrl-multi-cols input[type="checkbox"]');
        const needsMultiCols = ['heatmap', 'grouped_bar', 'stacked_bar'].includes(rec.chart_type);
        if (needsMultiCols && rec.columns.length > 0) {
            multiColsCbs.forEach(cb => {
                cb.checked = rec.columns.includes(cb.value);
            });
        }

        // If single Y column, also check it in multi-Y for convenience
        if (rec.y_column) {
            multiYCbs.forEach(cb => {
                if (cb.value === rec.y_column) cb.checked = true;
            });
        }

        updateVisibility(rec.chart_type);
    }

    /**
     * Show/hide X/Y selectors based on chart type needs.
     * Multi-Y types (line, scatter, area, bar) show checkbox list instead of single dropdown.
     */
    function updateVisibility(chartType) {
        const xGroup = document.getElementById('ctrl-x-group');
        const yGroup = document.getElementById('ctrl-y-group');
        const yMultiGroup = document.getElementById('ctrl-y-multi-group');
        const multiColsGroup = document.getElementById('ctrl-multi-cols-group');
        const aggGroup = document.getElementById('ctrl-aggregation-group');

        const needsMultiCols = ['heatmap', 'grouped_bar', 'stacked_bar'].includes(chartType);
        const supportsMultiY = ['line', 'scatter', 'area', 'bar'].includes(chartType);
        const needsX = !['box'].includes(chartType);
        const needsSingleY = ['pie', 'histogram', 'box'].includes(chartType);

        xGroup.style.display = needsX ? 'flex' : 'none';

        if (needsMultiCols) {
            // Heatmap / grouped bar — use the columns checkboxes
            yGroup.style.display = 'none';
            yMultiGroup.style.display = 'none';
            multiColsGroup.style.display = 'flex';
        } else if (supportsMultiY) {
            // Line / scatter / area / bar — show multi-Y checkboxes
            yGroup.style.display = 'none';
            yMultiGroup.style.display = 'flex';
            multiColsGroup.style.display = 'none';
        } else {
            // Single-Y types (pie, histogram, box)
            yGroup.style.display = needsSingleY ? 'flex' : 'none';
            yMultiGroup.style.display = 'none';
            multiColsGroup.style.display = 'none';
        }

        // Show aggregation only for bar/pie
        if (aggGroup) {
            aggGroup.style.display = ['bar', 'pie'].includes(chartType) ? 'flex' : 'none';
        }
    }

    /**
     * Collect current control values and send chart request to API.
     * Multi-Y columns are sent as comma-separated `columns` field.
     */
    function updateChart() {
        const sessionId = App.state.sessionId;
        if (!sessionId) {
            App.showToast('No data loaded. Please upload data first.', 'error');
            return;
        }

        const chartType = document.getElementById('ctrl-chart-type').value;
        const xColumn = document.getElementById('ctrl-x-column').value;
        const singleY = document.getElementById('ctrl-y-column').value;
        const title = document.getElementById('ctrl-title').value;
        const xLabel = document.getElementById('ctrl-x-label').value;
        const yLabel = document.getElementById('ctrl-y-label').value;
        const aggregation = document.getElementById('ctrl-aggregation').value;
        const colorScheme = document.getElementById('ctrl-color').value;

        // Collect multi-Y selections
        const multiYCols = [];
        document.querySelectorAll('#ctrl-y-multi input:checked').forEach(cb => {
            multiYCols.push(cb.value);
        });

        // Collect multi-columns (for heatmap/grouped bar)
        const multiCols = [];
        document.querySelectorAll('#ctrl-multi-cols input:checked').forEach(cb => {
            multiCols.push(cb.value);
        });

        const formData = new FormData();
        formData.append('session_id', sessionId);
        formData.append('chart_type', chartType);
        if (xColumn) formData.append('x_column', xColumn);
        if (title) formData.append('title', title);
        if (xLabel) formData.append('x_label', xLabel);
        if (yLabel) formData.append('y_label', yLabel);
        if (aggregation) formData.append('aggregation', aggregation);
        if (colorScheme) formData.append('color_scheme', colorScheme);

        // Determine which columns to send
        const needsMultiCols = ['heatmap', 'grouped_bar', 'stacked_bar'].includes(chartType);
        const supportsMultiY = ['line', 'scatter', 'area', 'bar'].includes(chartType);

        if (needsMultiCols && multiCols.length > 0) {
            formData.append('columns', multiCols.join(','));
        } else if (supportsMultiY && multiYCols.length > 0) {
            // Send multi-Y as columns list; first selected becomes y_column for backward compat
            formData.append('y_column', multiYCols[0]);
            formData.append('columns', multiYCols.join(','));
        } else if (singleY) {
            formData.append('y_column', singleY);
        }

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

    /**
     * Get current control panel values as a plain object (for template saving).
     */
    function getControlValues() {
        const chartType = document.getElementById('ctrl-chart-type').value;
        const xColumn = document.getElementById('ctrl-x-column').value;
        const singleY = document.getElementById('ctrl-y-column').value;
        const title = document.getElementById('ctrl-title').value;
        const xLabel = document.getElementById('ctrl-x-label').value;
        const yLabel = document.getElementById('ctrl-y-label').value;
        const aggregation = document.getElementById('ctrl-aggregation').value;
        const colorScheme = document.getElementById('ctrl-color').value;

        // Collect multi-Y selections
        const multiYCols = [];
        document.querySelectorAll('#ctrl-y-multi input:checked').forEach(cb => {
            multiYCols.push(cb.value);
        });

        // Collect multi-columns
        const multiCols = [];
        document.querySelectorAll('#ctrl-multi-cols input:checked').forEach(cb => {
            multiCols.push(cb.value);
        });

        return {
            chart_type: chartType,
            x_column: xColumn,
            y_column: singleY,
            columns: multiYCols.length > 0 ? multiYCols : multiCols,
            title: title,
            x_label: xLabel,
            y_label: yLabel,
            aggregation: aggregation,
            color_scheme: colorScheme,
        };
    }

    /**
     * Apply a saved template object to the control panel.
     */
    function applyTemplate(template) {
        const typeSelect = document.getElementById('ctrl-chart-type');
        const xSelect = document.getElementById('ctrl-x-column');
        const ySelect = document.getElementById('ctrl-y-column');
        const titleInput = document.getElementById('ctrl-title');
        const xLabelInput = document.getElementById('ctrl-x-label');
        const yLabelInput = document.getElementById('ctrl-y-label');
        const aggSelect = document.getElementById('ctrl-aggregation');
        const colorSelect = document.getElementById('ctrl-color');

        if (template.chart_type) typeSelect.value = template.chart_type;
        if (template.x_column) xSelect.value = template.x_column;
        if (template.y_column) ySelect.value = template.y_column;
        titleInput.value = template.title || '';
        xLabelInput.value = template.x_label || '';
        yLabelInput.value = template.y_label || '';
        aggSelect.value = template.aggregation || '';
        colorSelect.value = template.color_scheme || 'default';

        // Apply multi-Y checkboxes
        const multiYCbs = document.querySelectorAll('#ctrl-y-multi input[type="checkbox"]');
        multiYCbs.forEach(cb => {
            cb.checked = template.columns && template.columns.includes(cb.value);
        });

        // Apply multi-columns checkboxes
        const multiColsCbs = document.querySelectorAll('#ctrl-multi-cols input[type="checkbox"]');
        multiColsCbs.forEach(cb => {
            cb.checked = template.columns && template.columns.includes(cb.value);
        });

        updateVisibility(template.chart_type || 'bar');
    }

    return {
        populateColumns,
        setFromRecommendation,
        updateChart,
        updateVisibility,
        getControlValues,
        applyTemplate,
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

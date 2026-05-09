/**
 * DataViz — Chart Rendering Module
 * Renders Plotly.js charts in the gallery, workspace, and fullscreen mode.
 * Optimized for large datasets with zoom, pan, height control, and fullscreen.
 */

const ChartModule = (() => {
    // Shared Plotly config — enables scroll zoom and pan for exploring large data
    const PLOTLY_CONFIG = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        displaylogo: false,
        scrollZoom: true,
        toImageButtonOptions: {
            format: 'png',
            filename: 'dataviz_chart',
            height: 800,
            width: 1200,
            scale: 2,
        },
    };

    // Track the current chart data/layout for fullscreen re-render
    let _currentData = null;
    let _currentLayout = null;

    /**
     * Render the chart gallery with thumbnail previews.
     */
    function renderGallery(recommendations) {
        const section = document.getElementById('chart-gallery-section');
        const grid = document.getElementById('chart-grid');
        const workspace = document.getElementById('chart-workspace-section');

        section.style.display = 'block';
        workspace.style.display = 'none';
        section.classList.add('fade-in');
        grid.innerHTML = '';

        recommendations.forEach((rec, idx) => {
            const card = document.createElement('div');
            card.className = 'chart-thumb';
            card.innerHTML = `
                <div class="chart-thumb-plot" id="thumb-${idx}"></div>
                <div class="chart-thumb-info">
                    <div class="chart-thumb-title">${App.escapeHtml(rec.title)}</div>
                    <div class="chart-thumb-desc">${App.escapeHtml(rec.description)}</div>
                </div>
            `;
            card.addEventListener('click', () => openInWorkspace(rec, idx));
            grid.appendChild(card);

            // Render thumbnail chart
            setTimeout(() => {
                const thumbLayout = {
                    ...rec.plotly_config.layout,
                    margin: { l: 40, r: 15, t: 35, b: 40 },
                    title: { text: rec.title, font: { size: 13 } },
                    showlegend: false,
                    font: { size: 10, family: 'Inter, system-ui, sans-serif', color: '#e2e8f0' },
                };
                Plotly.newPlot(`thumb-${idx}`, rec.plotly_config.data, thumbLayout, {
                    ...PLOTLY_CONFIG,
                    displayModeBar: false,
                    staticPlot: true,
                    scrollZoom: false,
                });
            }, 50 * idx);
        });
    }

    /**
     * Open a chart in the full workspace view.
     */
    function openInWorkspace(rec, idx) {
        const gallery = document.getElementById('chart-gallery-section');
        const workspace = document.getElementById('chart-workspace-section');

        gallery.style.display = 'none';
        workspace.style.display = 'block';
        workspace.classList.add('fade-in');

        App.state.currentChart = rec;

        // Set control values from recommendation
        Controls.setFromRecommendation(rec);

        // Render full chart
        renderMainChart(rec.plotly_config.data, rec.plotly_config.layout);

        // Scroll to workspace
        workspace.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    /**
     * Render chart in the main workspace with large-data-friendly settings.
     */
    function renderMainChart(data, layout) {
        const container = document.getElementById('main-chart');
        const fullLayout = {
            ...layout,
            margin: { l: 60, r: 30, t: 60, b: 60 },
            title: { ...layout.title, font: { size: 18 } },
            font: { size: 13, family: 'Inter, system-ui, sans-serif', color: '#e2e8f0' },
            autosize: true,
            // Enable drag-to-zoom and double-click-to-reset for exploring data
            dragmode: 'zoom',
        };

        // Store for fullscreen re-render
        _currentData = data;
        _currentLayout = fullLayout;

        Plotly.newPlot(container, data, fullLayout, PLOTLY_CONFIG);
    }

    /**
     * Open fullscreen view with the current chart.
     */
    function enterFullscreen() {
        if (!_currentData || !_currentLayout) {
            App.showToast('No chart to expand. Select a chart first.', 'error');
            return;
        }

        const overlay = document.getElementById('fullscreen-overlay');
        const fsChart = document.getElementById('fullscreen-chart');
        const fsTitle = document.getElementById('fullscreen-title');

        // Set title from current layout
        const titleText = _currentLayout.title?.text || 'Chart';
        fsTitle.textContent = titleText;

        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';

        // Render in fullscreen container with generous margins
        const fsLayout = {
            ..._currentLayout,
            margin: { l: 80, r: 50, t: 70, b: 70 },
            title: { ..._currentLayout.title, font: { size: 22 } },
            font: { size: 14, family: 'Inter, system-ui, sans-serif', color: '#e2e8f0' },
            autosize: true,
            dragmode: 'zoom',
        };

        // Small delay to allow CSS transition/display to settle
        requestAnimationFrame(() => {
            Plotly.newPlot(fsChart, _currentData, fsLayout, {
                ...PLOTLY_CONFIG,
                toImageButtonOptions: {
                    format: 'png',
                    filename: 'dataviz_chart_fullscreen',
                    height: 1200,
                    width: 1920,
                    scale: 2,
                },
            });
        });
    }

    /**
     * Exit fullscreen view.
     */
    function exitFullscreen() {
        const overlay = document.getElementById('fullscreen-overlay');
        const fsChart = document.getElementById('fullscreen-chart');

        overlay.classList.remove('active');
        document.body.style.overflow = '';

        // Purge the fullscreen plotly instance to free memory
        Plotly.purge(fsChart);
    }

    /**
     * Set the chart container height (inline workspace).
     */
    function setChartHeight(height) {
        const container = document.getElementById('main-chart');
        container.style.minHeight = height + 'px';

        // Trigger Plotly resize to fill the new height
        Plotly.Plots.resize(container);
    }

    /**
     * Reset zoom on the main workspace chart.
     */
    function resetZoom() {
        const container = document.getElementById('main-chart');
        Plotly.relayout(container, {
            'xaxis.autorange': true,
            'yaxis.autorange': true,
        });
    }

    /**
     * Reset zoom on the fullscreen chart.
     */
    function resetZoomFullscreen() {
        const fsChart = document.getElementById('fullscreen-chart');
        Plotly.relayout(fsChart, {
            'xaxis.autorange': true,
            'yaxis.autorange': true,
        });
    }

    /**
     * Export the fullscreen chart as PNG.
     */
    function exportFullscreenPng() {
        const fsChart = document.getElementById('fullscreen-chart');
        Plotly.downloadImage(fsChart, {
            format: 'png',
            width: 1920,
            height: 1200,
            scale: 2,
            filename: 'dataviz_chart_fullscreen',
        });
    }

    /**
     * Export the main chart as PNG.
     */
    function exportPng() {
        const container = document.getElementById('main-chart');
        Plotly.downloadImage(container, {
            format: 'png',
            width: 1200,
            height: 800,
            scale: 2,
            filename: 'dataviz_chart',
        });
    }

    return {
        renderGallery,
        openInWorkspace,
        renderMainChart,
        enterFullscreen,
        exitFullscreen,
        setChartHeight,
        resetZoom,
        resetZoomFullscreen,
        exportFullscreenPng,
        exportPng,
    };
})();

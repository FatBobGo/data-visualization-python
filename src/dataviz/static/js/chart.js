/**
 * DataViz — Chart Rendering Module
 * Renders Plotly.js charts in the gallery and workspace.
 */

const ChartModule = (() => {
    const PLOTLY_CONFIG = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        displaylogo: false,
        toImageButtonOptions: {
            format: 'png',
            filename: 'dataviz_chart',
            height: 800,
            width: 1200,
            scale: 2,
        },
    };

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
     * Render chart in the main workspace.
     */
    function renderMainChart(data, layout) {
        const container = document.getElementById('main-chart');
        const fullLayout = {
            ...layout,
            margin: { l: 60, r: 30, t: 60, b: 60 },
            title: { ...layout.title, font: { size: 18 } },
            font: { size: 13, family: 'Inter, system-ui, sans-serif', color: '#e2e8f0' },
            autosize: true,
        };

        Plotly.newPlot(container, data, fullLayout, PLOTLY_CONFIG);
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
        exportPng,
    };
})();

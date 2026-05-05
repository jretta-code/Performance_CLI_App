import json
import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def generate_html_report(global_metrics, url_metrics, included_requests, metadata, output_path):
    logger.info("Generando reporte HTML...")
    
    # We enumerate the URLs to have URL 1, URL 2, etc.
    url_items = list(url_metrics.items())
    
    url_sections_html = ""
    summary_rows_html = ""
    
    summary_chart_data = []

    for idx, (url, m) in enumerate(url_items, 1):
        url_label = f"URL {idx}"
        base_endpoint = m['base_endpoint']
        selects = m['selects']
        filters = m['filters']
        
        # Details HTML
        selects_html = f"<p><strong>$selects:</strong> {selects}</p>" if selects else ""
        filters_html = f"<p><strong>$filters:</strong> {filters}</p>" if filters else ""
        
        table_html = f"""
        <table class="table table-striped table-bordered table-sm mt-3">
            <thead class="table-dark">
                <tr><th>Count</th><th>Min (ms)</th><th>Max (ms)</th><th>Avg (ms)</th><th>P50 (ms)</th><th>P90 (ms)</th><th>P95 (ms)</th><th>P99 (ms)</th></tr>
            </thead>
            <tbody>
                <tr>
                    <td>{m['count']}</td>
                    <td>{m['min']:.2f}</td>
                    <td>{m['max']:.2f}</td>
                    <td>{m['avg']:.2f}</td>
                    <td>{m['p50']:.2f}</td>
                    <td>{m['p90']:.2f}</td>
                    <td>{m['p95']:.2f}</td>
                    <td>{m['p99']:.2f}</td>
                </tr>
            </tbody>
        </table>
        """
        
        # Chart for this URL: min/max for Queueing, Conn, Req sent, Svr response, Cont Download, Total
        categories = ['Queueing', 'Conn', 'Req sent', 'Svr response', 'Cont Download', 'Total']
        min_vals = [
            m['queueing_min'], m['conn_min'], m['req_sent_min'], 
            m['svr_response_min'], m['cont_download_min'], m['min']
        ]
        max_vals = [
            m['queueing_max'], m['conn_max'], m['req_sent_max'], 
            m['svr_response_max'], m['cont_download_max'], m['max']
        ]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=categories, y=min_vals, name='Min', marker_color='rgb(55, 83, 109)'))
        fig.add_trace(go.Bar(x=categories, y=max_vals, name='Max', marker_color='rgb(26, 118, 255)'))
        fig.update_layout(
            title=f"Tiempos Min/Max por Fase - {url_label}",
            barmode='group',
            yaxis_title="Tiempo (ms)",
            margin=dict(t=40, b=20, l=40, r=20)
        )
        chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn' if idx == 1 else False)
        
        url_sections_html += f"""
        <div class="card mb-5 shadow-sm">
            <div class="card-header bg-primary text-white">
                <h4 class="mb-0">{url_label} - {base_endpoint}</h4>
            </div>
            <div class="card-body">
                {selects_html}
                {filters_html}
                <div class="table-responsive">
                    {table_html}
                </div>
                <div class="mt-4">
                    {chart_html}
                </div>
            </div>
        </div>
        """
        
        # Prepare data for summary table
        params_html = ""
        if selects: params_html += f"<br><small class='text-muted'>$select: {selects}</small>"
        if filters: params_html += f"<br><small class='text-muted'>$filter: {filters}</small>"
        
        summary_rows_html += f"""
        <tr>
            <td>{url_label}</td>
            <td style="word-break: break-all;">{base_endpoint}{params_html}</td>
            <td>{m['count']}</td>
            <td>{m['min']:.2f}</td>
            <td>{m['max']:.2f}</td>
            <td>{m['avg']:.2f}</td>
            <td>{m['p50']:.2f}</td>
            <td>{m['p90']:.2f}</td>
            <td>{m['p95']:.2f}</td>
            <td>{m['p99']:.2f}</td>
        </tr>
        """
        
        # Prepare data for summary chart
        summary_chart_data.append({
            'URL': url_label,
            'Min Total': m['min'],
            'Max Total': m['max']
        })
        
    # Summary Chart
    summary_chart_html = ""
    if summary_chart_data:
        df_summary = pd.DataFrame(summary_chart_data)
        fig_sum = go.Figure()
        fig_sum.add_trace(go.Bar(x=df_summary['URL'], y=df_summary['Min Total'], name='Min Total', marker_color='rgb(55, 83, 109)'))
        fig_sum.add_trace(go.Bar(x=df_summary['URL'], y=df_summary['Max Total'], name='Max Total', marker_color='rgb(26, 118, 255)'))
        fig_sum.update_layout(
            title="Min y Max (Total) por URL",
            barmode='group',
            xaxis_title="URL",
            yaxis_title="Tiempo Total (ms)"
        )
        summary_chart_html = fig_sum.to_html(full_html=False, include_plotlyjs=False)

    metadata_html = f"""
    <div class="alert alert-info">
        <strong>Fecha de Análisis:</strong> {metadata.get('date')}<br>
        <strong>Archivos Procesados:</strong> {metadata.get('files_processed')}<br>
        <strong>Filtros Aplicados:</strong> {', '.join(metadata.get('filters', [])) if metadata.get('filters') else 'Ninguno'}
    </div>
    """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reporte HAR Analytics</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script charset="utf-8" src="https://cdn.plot.ly/plotly-3.5.0.min.js" integrity="sha256-fHbNLP+GlIXN+efbQec78UkemUz3NJp7UmfGxC1tNxs=" crossorigin="anonymous"></script>
    </head>
    <body class="bg-light">
        <div class="container my-5">
            <h1 class="mb-4">Reporte de Performance HAR</h1>
            {metadata_html}
            
            <h2 class="mt-5 mb-4 border-bottom pb-2">Resumen General</h2>
            <div class="card shadow-sm mb-5">
                <div class="card-body">
                    <div class="table-responsive mb-4">
                        <table class="table table-striped table-bordered table-hover align-middle">
                            <thead class="table-dark">
                                <tr>
                                    <th>Número</th>
                                    <th>Endpoint / Params</th>
                                    <th>Count</th>
                                    <th>Min (ms)</th>
                                    <th>Max (ms)</th>
                                    <th>Avg (ms)</th>
                                    <th>P50</th>
                                    <th>P90</th>
                                    <th>P95</th>
                                    <th>P99</th>
                                </tr>
                            </thead>
                            <tbody>
                                {summary_rows_html}
                            </tbody>
                        </table>
                    </div>
                    <div>
                        {summary_chart_html}
                    </div>
                </div>
            </div>

            <h2 class="mt-5 mb-4 border-bottom pb-2">Resumen por URL</h2>
            {url_sections_html}
            
        </div>
    </body>
    </html>
    """
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"Reporte HTML guardado exitosamente en: {output_path}")
    except Exception as e:
        logger.error(f"Error al guardar el reporte HTML: {e}")

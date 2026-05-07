import json
import datetime
import plotly.graph_objects as go
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def _pct_improvement(val1, val2):
    """
    Calcula el % de mejora de val2 respecto a val1.
    Positivo = val2 es más rápido (mejoró).
    Negativo = val2 es más lento (empeoró).
    """
    if val1 == 0:
        return 0.0
    return ((val1 - val2) / val1) * 100.0


def _improvement_cell(pct):
    """Retorna HTML de la celda de % mejora con color según el valor."""
    if pct > 0:
        color = "#d4edda"   # verde claro
        text_color = "#155724"
        arrow = "▼"
        label = f"{arrow} {pct:.1f}% más rápido"
    elif pct < 0:
        color = "#f8d7da"   # rojo claro
        text_color = "#721c24"
        arrow = "▲"
        label = f"{arrow} {abs(pct):.1f}% más lento"
    else:
        color = "#fff3cd"   # amarillo
        text_color = "#856404"
        label = "Sin cambio"
    return f'<td style="background:{color}; color:{text_color}; font-weight:600;">{label}</td>'


def generate_html_report(gm1, um1, ir1, gm2, um2, ir2, metadata, output_path):
    logger.info("Generando reporte HTML comparativo...")

    folder1 = metadata.get('folder1_name', 'Carpeta 1')
    folder2 = metadata.get('folder2_name', 'Carpeta 2')

    # ------------------------------------------------------------------ #
    # Construir conjunto de URLs unión ordenado (por base_endpoint de um1) #
    # ------------------------------------------------------------------ #
    all_urls = sorted(
        set(list(um1.keys()) + list(um2.keys())),
        key=lambda u: (um1.get(u, um2.get(u, {})).get('base_endpoint', u))
    )

    # ------------------------------------------------------------------ #
    # RESUMEN GENERAL – tabla                                              #
    # ------------------------------------------------------------------ #
    summary_rows_html = ""
    summary_chart_labels = []
    summary_chart_min1 = []
    summary_chart_min2 = []

    for idx, url in enumerate(all_urls, 1):
        url_label = f"URL {idx}"
        m1 = um1.get(url)
        m2 = um2.get(url)

        base_endpoint = (m1 or m2).get('base_endpoint', url)
        selects = (m1 or m2).get('selects', '')
        filters_val = (m1 or m2).get('filters', '')

        params_html = ""
        if selects:
            params_html += f"<br><small class='text-muted'>$select: {selects}</small>"
        if filters_val:
            params_html += f"<br><small class='text-muted'>$filter: {filters_val}</small>"

        min1 = m1['min'] if m1 else None
        avg1 = m1['avg'] if m1 else None
        min2 = m2['min'] if m2 else None
        avg2 = m2['avg'] if m2 else None

        def _fmt(v):
            return f"{v:.2f}" if v is not None else "N/D"

        # % mejora basado en avg (si ambos disponibles)
        if min1 is not None and min2 is not None:
            pct_min = _pct_improvement(min1, min2)
            pct_avg = _pct_improvement(avg1, avg2)
            # Mostramos mejora promedio de min y avg
            pct_overall = (pct_min + pct_avg) / 2
            improve_cell = _improvement_cell(pct_overall)
        else:
            improve_cell = "<td>N/D</td>"

        summary_rows_html += f"""
        <tr>
            <td>{url_label}</td>
            <td style="word-break: break-all;">{base_endpoint}{params_html}</td>
            <td>{_fmt(min1)}</td>
            <td>{_fmt(avg1)}</td>
            <td>{_fmt(min2)}</td>
            <td>{_fmt(avg2)}</td>
            {improve_cell}
        </tr>
        """

        # datos para gráfica de resumen general (min total)
        summary_chart_labels.append(url_label)
        summary_chart_min1.append(min1 if min1 is not None else 0)
        summary_chart_min2.append(min2 if min2 is not None else 0)

    # ------------------------------------------------------------------ #
    # RESUMEN GENERAL – gráfica comparación de Min por URL                #
    # ------------------------------------------------------------------ #
    summary_chart_html = ""
    if summary_chart_labels:
        fig_sum = go.Figure()
        fig_sum.add_trace(go.Bar(
            x=summary_chart_labels,
            y=summary_chart_min1,
            name=folder1,
            marker_color='rgb(55, 83, 109)'
        ))
        fig_sum.add_trace(go.Bar(
            x=summary_chart_labels,
            y=summary_chart_min2,
            name=folder2,
            marker_color='rgb(26, 118, 255)'
        ))
        fig_sum.update_layout(
            title=f"Comparación de tiempos entre {folder1} y {folder2}",
            barmode='group',
            xaxis_title="URL",
            yaxis_title="Tiempo Total (ms)",
            legend=dict(orientation="v", x=1.01, y=1),
            margin=dict(t=50, b=40, l=50, r=120),
            plot_bgcolor='rgb(235,240,248)',
            paper_bgcolor='rgb(245,248,252)'
        )
        summary_chart_html = fig_sum.to_html(full_html=False, include_plotlyjs=False)

    # ------------------------------------------------------------------ #
    # RESUMEN POR URL – secciones                                          #
    # ------------------------------------------------------------------ #
    url_sections_html = ""
    plotlyjs_included = False   # el CDN ya se carga en el <head>

    for idx, url in enumerate(all_urls, 1):
        url_label = f"URL {idx}"
        m1 = um1.get(url)
        m2 = um2.get(url)

        base_endpoint = (m1 or m2).get('base_endpoint', url)
        selects = (m1 or m2).get('selects', '')
        filters_val = (m1 or m2).get('filters', '')

        selects_html = f"<p><strong>$selects:</strong> {selects}</p>" if selects else ""
        filters_html_str = f"<p><strong>$filters:</strong> {filters_val}</p>" if filters_val else ""

        def _fmt(v):
            return f"{v:.2f}" if v is not None else "N/D"

        min1 = m1['min'] if m1 else None
        avg1 = m1['avg'] if m1 else None
        min2 = m2['min'] if m2 else None
        avg2 = m2['avg'] if m2 else None

        if min1 is not None and min2 is not None:
            pct_min = _pct_improvement(min1, min2)
            pct_avg = _pct_improvement(avg1, avg2)
            pct_overall = (pct_min + pct_avg) / 2
            improve_cell = _improvement_cell(pct_overall)
        else:
            improve_cell = "<td>N/D</td>"

        # Sub-tabla comparativa para esta URL
        url_table_html = f"""
        <table class="table table-striped table-bordered table-sm mt-3">
            <thead>
                <tr>
                    <th rowspan="2">Número</th>
                    <th rowspan="2">Endpoint / Params</th>
                    <th colspan="2" class="text-center">{folder1}</th>
                    <th colspan="2" class="text-center">{folder2}</th>
                    <th rowspan="2">% Mejora</th>
                </tr>
                <tr>
                    <th>Min (ms)</th>
                    <th>Avg (ms)</th>
                    <th>Min (ms)</th>
                    <th>Avg (ms)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>{url_label}</td>
                    <td style="word-break: break-all;">{base_endpoint}</td>
                    <td>{_fmt(min1)}</td>
                    <td>{_fmt(avg1)}</td>
                    <td>{_fmt(min2)}</td>
                    <td>{_fmt(avg2)}</td>
                    {improve_cell}
                </tr>
            </tbody>
        </table>
        """

        # Gráfica por URL: comparación min por fase (Queueing, Conn, Req sent, Svr response, Cont Download, Total)
        categories = ['Queueing', 'Conn', 'Req sent', 'Svr response', 'Cont Download', 'Total']

        def _phase_mins(m):
            if m is None:
                return [0] * 6
            return [
                m.get('queueing_min', 0),
                m.get('conn_min', 0),
                m.get('req_sent_min', 0),
                m.get('svr_response_min', 0),
                m.get('cont_download_min', 0),
                m.get('min', 0)
            ]

        vals1 = _phase_mins(m1)
        vals2 = _phase_mins(m2)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=categories,
            y=vals1,
            name=folder1,
            marker_color='rgb(55, 83, 109)'
        ))
        fig.add_trace(go.Bar(
            x=categories,
            y=vals2,
            name=folder2,
            marker_color='rgb(26, 118, 255)'
        ))
        fig.update_layout(
            title=f"Comparación de tiempos entre {folder1} y {folder2} de {url_label}",
            barmode='group',
            yaxis_title="Tiempo (ms)",
            legend=dict(orientation="v", x=1.01, y=1),
            margin=dict(t=50, b=20, l=50, r=120),
            plot_bgcolor='rgb(235,240,248)',
            paper_bgcolor='rgb(245,248,252)'
        )
        chart_html = fig.to_html(full_html=False, include_plotlyjs=False)

        url_sections_html += f"""
        <div class="card mb-5 shadow-sm">
            <div class="card-header bg-primary text-white">
                <h4 class="mb-0">{url_label} - {base_endpoint}</h4>
            </div>
            <div class="card-body">
                {selects_html}
                {filters_html_str}
                <div class="table-responsive">
                    {url_table_html}
                </div>
                <div class="mt-4">
                    {chart_html}
                </div>
            </div>
        </div>
        """

    # ------------------------------------------------------------------ #
    # METADATA                                                             #
    # ------------------------------------------------------------------ #
    filters_applied = ', '.join(metadata.get('filters', []) or []) or 'Ninguno'
    metadata_html = f"""
    <div class="alert alert-info">
        <strong>Fecha de Análisis:</strong> {metadata.get('date')}<br>
        <strong>Carpeta 1 ({folder1}):</strong> {metadata.get('files1_processed')} archivos HAR procesados<br>
        <strong>Carpeta 2 ({folder2}):</strong> {metadata.get('files2_processed')} archivos HAR procesados<br>
        <strong>Filtros Aplicados:</strong> {filters_applied}
    </div>
    """

    # ------------------------------------------------------------------ #
    # HTML FINAL                                                           #
    # ------------------------------------------------------------------ #
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte HAR Analytics – Comparación</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script charset="utf-8" src="https://cdn.plot.ly/plotly-3.5.0.min.js" integrity="sha256-fHbNLP+GlIXN+efbQec78UkemUz3NJp7UmfGxC1tNxs=" crossorigin="anonymous"></script>
    <style>
        /* Encabezados dobles en tabla */
        thead tr:first-child th {{ background: #212529; color: #fff; text-align: center; }}
        thead tr:nth-child(2) th {{ background: #343a40; color: #fff; text-align: center; }}
    </style>
</head>
<body class="bg-light">
    <div class="container my-5">
        <h1 class="mb-4">Reporte de Performance HAR – Comparación</h1>
        <h5 class="text-muted mb-4">{folder1} vs {folder2}</h5>
        {metadata_html}

        <h2 class="mt-5 mb-4 border-bottom pb-2">Resumen General</h2>
        <div class="card shadow-sm mb-5">
            <div class="card-body">
                <div class="table-responsive mb-4">
                    <table class="table table-striped table-bordered table-hover align-middle">
                        <thead>
                            <tr>
                                <th rowspan="2">Número</th>
                                <th rowspan="2">Endpoint / Params</th>
                                <th colspan="2" class="text-center">{folder1}</th>
                                <th colspan="2" class="text-center">{folder2}</th>
                                <th rowspan="2">% Mejora</th>
                            </tr>
                            <tr>
                                <th>Min (ms)</th>
                                <th>Avg (ms)</th>
                                <th>Min (ms)</th>
                                <th>Avg (ms)</th>
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

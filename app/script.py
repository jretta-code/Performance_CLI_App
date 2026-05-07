import argparse
import sys
import logging
import datetime
import os

from har_reader import discover_har_files, parse_har_file
from filters import apply_filters
from stats import aggregate_stats
from report_html import generate_html_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_folder(folder_path, filter_patterns):
    """Descubre, parsea, filtra y agrega estadísticas de una carpeta HAR."""
    if not os.path.exists(folder_path):
        logger.error(f"La ruta '{folder_path}' no existe.")
        sys.exit(1)

    har_files = discover_har_files(folder_path)
    if not har_files:
        logger.error(f"No se encontraron archivos .har en '{folder_path}'")
        sys.exit(1)

    logger.info(f"[{folder_path}] Se encontraron {len(har_files)} archivos HAR.")

    all_requests = []
    total_errors = 0
    for file in har_files:
        reqs, errors = parse_har_file(file)
        all_requests.extend(reqs)
        total_errors += errors

    logger.info(f"[{folder_path}] Total requests leídas: {len(all_requests)}. Errores: {total_errors}")

    filtered_requests, included, excluded = apply_filters(all_requests, filter_patterns)
    logger.info(f"[{folder_path}] Requests filtradas: {included} incluidas, {excluded} excluidas.")

    if included == 0:
        logger.warning(f"[{folder_path}] Ninguna request sobrevivió a los filtros.")
        sys.exit(0)

    global_metrics, url_metrics, included_requests_data = aggregate_stats(filtered_requests)
    logger.info(f"[{folder_path}] URLs agrupadas: {len(url_metrics)}")

    return global_metrics, url_metrics, included_requests_data, len(har_files)

def main():
    parser = argparse.ArgumentParser(description="Analizador HAR a HTML - Modo Comparación")
    parser.add_argument("input1", help="Ruta a la primera carpeta de archivos HAR (línea base)")
    parser.add_argument("input2", help="Ruta a la segunda carpeta de archivos HAR (comparación)")
    parser.add_argument("--filter", action="append", help="Filtros mixtos (substring o regex) para aplicar a las URLs. Puede usarse múltiples veces.")
    parser.add_argument("--output", default="report.html", help="Ruta de salida para el reporte HTML (default: report.html)")

    args = parser.parse_args()

    folder1_name = os.path.basename(os.path.normpath(args.input1))
    folder2_name = os.path.basename(os.path.normpath(args.input2))

    # Cargar ambas carpetas
    logger.info("=== Procesando Carpeta 1 ===")
    gm1, um1, ir1, files1 = load_folder(args.input1, args.filter)

    logger.info("=== Procesando Carpeta 2 ===")
    gm2, um2, ir2, files2 = load_folder(args.input2, args.filter)

    # Metadata del reporte
    metadata = {
        'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'folder1_name': folder1_name,
        'folder2_name': folder2_name,
        'files1_processed': files1,
        'files2_processed': files2,
        'filters': args.filter
    }

    # Generar reporte comparativo
    generate_html_report(gm1, um1, ir1, gm2, um2, ir2, metadata, args.output)

    logger.info("Ejecución finalizada con éxito.")
    sys.exit(0)

if __name__ == "__main__":
    main()

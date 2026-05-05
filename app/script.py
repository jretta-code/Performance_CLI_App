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

def main():
    parser = argparse.ArgumentParser(description="Analizador HAR a HTML")
    parser.add_argument("input", help="Ruta al archivo HAR o directorio de archivos HAR")
    parser.add_argument("--filter", action="append", help="Filtros mixtos (substring o regex) para aplicar a las URLs. Puede usarse múltiples veces.")
    parser.add_argument("--output", default="report.html", help="Ruta de salida para el reporte HTML (default: report.html)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        logger.error(f"La ruta de entrada '{args.input}' no existe.")
        sys.exit(1)
        
    # Fase 1: Descubrimiento y Parseo
    har_files = discover_har_files(args.input)
    if not har_files:
        logger.error(f"No se encontraron archivos .har en '{args.input}'")
        sys.exit(1)
        
    logger.info(f"Se encontraron {len(har_files)} archivos HAR.")
    
    all_requests = []
    total_errors = 0
    for file in har_files:
        reqs, errors = parse_har_file(file)
        all_requests.extend(reqs)
        total_errors += errors
        
    logger.info(f"Total de requests leídas: {len(all_requests)}. Errores de parseo: {total_errors}")
    
    if not all_requests:
        logger.warning("No se extrajeron requests de los archivos proporcionados.")
        # We can still generate an empty report, but maybe not very useful
        
    # Fase 2: Filtros
    filtered_requests, included, excluded = apply_filters(all_requests, args.filter)
    logger.info(f"Requests filtradas: {included} incluidas, {excluded} excluidas.")
    
    if included == 0:
        logger.warning("Ninguna request sobrevivió a los filtros.")
        sys.exit(0)
        
    # Fase 3: Estadísticas
    global_metrics, url_metrics, included_requests_data = aggregate_stats(filtered_requests)
    logger.info(f"URLs agrupadas: {len(url_metrics)}")
    
    # Fase 4: Reporte HTML
    metadata = {
        'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'files_processed': len(har_files),
        'filters': args.filter
    }
    
    generate_html_report(global_metrics, url_metrics, included_requests_data, metadata, args.output)
    
    logger.info("Ejecución finalizada con éxito.")
    sys.exit(0)

if __name__ == "__main__":
    main()

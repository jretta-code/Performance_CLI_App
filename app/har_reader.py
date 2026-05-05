import os
import json
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def discover_har_files(input_path):
    har_files = []
    if os.path.isfile(input_path) and input_path.lower().endswith('.har'):
        har_files.append(input_path)
    elif os.path.isdir(input_path):
        for root, _, files in os.walk(input_path):
            for file in files:
                if file.lower().endswith('.har'):
                    har_files.append(os.path.join(root, file))
    return har_files

def parse_har_file(file_path):
    requests = []
    errors = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        entries = data.get('log', {}).get('entries', [])
        for entry in entries:
            try:
                req = entry.get('request', {})
                res = entry.get('response', {})
                
                from urllib.parse import unquote, urlparse, parse_qs
                
                url = req.get('url', '')
                if not url:
                    continue
                    
                decoded_url = unquote(url)
                parsed_url = urlparse(decoded_url)
                
                # Extract base endpoint
                base_endpoint = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                
                # Extract query params
                query_params = parse_qs(parsed_url.query)
                selects = query_params.get('$select', [])
                filters = query_params.get('$filter', [])
                
                # Extract timings
                timings = entry.get('timings', {})
                queueing = max(0, timings.get('blocked', 0))
                conn = max(0, timings.get('connect', 0))
                req_sent = max(0, timings.get('send', 0))
                svr_response = max(0, timings.get('wait', 0))
                cont_download = max(0, timings.get('receive', 0))
                total_time = entry.get('time', 0.0)

                # Extract normalized fields
                normalized_request = {
                    'url': decoded_url,
                    'base_endpoint': base_endpoint,
                    'selects': selects[0] if selects else '',
                    'filters': filters[0] if filters else '',
                    'method': req.get('method', ''),
                    'status': res.get('status', 0),
                    'time': total_time,
                    'queueing': queueing,
                    'conn': conn,
                    'req_sent': req_sent,
                    'svr_response': svr_response,
                    'cont_download': cont_download,
                    'size': res.get('bodySize', 0) + res.get('headersSize', 0),
                    'startedDateTime': entry.get('startedDateTime', ''),
                    'origin_file': file_path
                }
                requests.append(normalized_request)
            except Exception as e:
                errors += 1
                logger.debug(f"Error parsing entry in {file_path}: {e}")
                
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        errors += 1
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        errors += 1
        
    return requests, errors

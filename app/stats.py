import statistics
from collections import defaultdict

def calculate_percentile(data, percentile):
    if not data:
        return 0
    data = sorted(data)
    k = (len(data) - 1) * (percentile / 100.0)
    f = int(k)
    c = f + 1
    if f == c or c >= len(data):
        return data[f]
    return data[f] + (data[c] - data[f]) * (k - f)

def calculate_metrics(reqs):
    if not reqs:
        return {
            'count': 0, 'min': 0, 'max': 0, 'avg': 0,
            'p50': 0, 'p90': 0, 'p95': 0, 'p99': 0,
            'queueing_min': 0, 'queueing_max': 0,
            'conn_min': 0, 'conn_max': 0,
            'req_sent_min': 0, 'req_sent_max': 0,
            'svr_response_min': 0, 'svr_response_max': 0,
            'cont_download_min': 0, 'cont_download_max': 0
        }
    
    times = [r['time'] for r in reqs]
    queueings = [r['queueing'] for r in reqs]
    conns = [r['conn'] for r in reqs]
    req_sents = [r['req_sent'] for r in reqs]
    svr_responses = [r['svr_response'] for r in reqs]
    cont_downloads = [r['cont_download'] for r in reqs]
    
    return {
        'base_endpoint': reqs[0]['base_endpoint'] if reqs else '',
        'selects': reqs[0]['selects'] if reqs else '',
        'filters': reqs[0]['filters'] if reqs else '',
        'count': len(times),
        'min': min(times),
        'max': max(times),
        'avg': sum(times) / len(times),
        'p50': calculate_percentile(times, 50),
        'p90': calculate_percentile(times, 90),
        'p95': calculate_percentile(times, 95),
        'p99': calculate_percentile(times, 99),
        'queueing_min': min(queueings), 'queueing_max': max(queueings),
        'conn_min': min(conns), 'conn_max': max(conns),
        'req_sent_min': min(req_sents), 'req_sent_max': max(req_sents),
        'svr_response_min': min(svr_responses), 'svr_response_max': max(svr_responses),
        'cont_download_min': min(cont_downloads), 'cont_download_max': max(cont_downloads)
    }

def aggregate_stats(requests):
    included_requests = [req for req in requests if req.get('included', True)]
    
    # Global metrics
    global_metrics = calculate_metrics(included_requests)
    
    # Per URL metrics
    url_groups = defaultdict(list)
    for req in included_requests:
        url_groups[req['url']].append(req)
        
    url_metrics = {}
    for url, reqs in url_groups.items():
        url_metrics[url] = calculate_metrics(reqs)
        
    # Sort URLs alphabetically by base_endpoint
    sorted_urls = sorted(url_metrics.items(), key=lambda x: x[1]['base_endpoint'])
    sorted_url_metrics = {url: metrics for url, metrics in sorted_urls}
    
    return global_metrics, sorted_url_metrics, included_requests

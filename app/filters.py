import re
import logging

logger = logging.getLogger(__name__)

class MixedFilter:
    def __init__(self, pattern):
        self.pattern_str = pattern
        self.regex = None
        try:
            self.regex = re.compile(pattern)
        except re.error:
            logger.warning(f"Invalid regex pattern '{pattern}', falling back to substring match only.")

    def match(self, text):
        if self.pattern_str in text:
            return True
        if self.regex and self.regex.search(text):
            return True
        return False

def apply_filters(requests, filter_patterns):
    if not filter_patterns:
        # If no filters, include all
        for req in requests:
            req['included'] = True
        return requests, len(requests), 0
        
    filters = [MixedFilter(p) for p in filter_patterns]
    
    included_count = 0
    excluded_count = 0
    
    for req in requests:
        url = req.get('url', '')
        matched = any(f.match(url) for f in filters)
        req['included'] = matched
        
        if matched:
            included_count += 1
        else:
            excluded_count += 1
            
    return requests, included_count, excluded_count

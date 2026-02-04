# check_dbt_tests.py
import json

def parse_dbt_results(results_path):
    """Parse dbt run_results.json"""
    with open(results_path) as f:
        results = json.load(f)
    
    # Count failures by severity
    errors = []
    warnings = []
    
    for result in results.get('results', []):
        if result['status'] == 'fail':
            # Check severity (if available)
            severity = result.get('config', {}).get('severity', 'error')
            
            if severity == 'error':
                errors.append(result)
            else:
                warnings.append(result)
    
    return errors, warnings

import dns.resolver
import requests
import yaml
import json
from datetime import datetime, timedelta

def load_domain_config():
    with open('domain_config.yml', 'r') as file:
        return yaml.safe_load(file)

def check_domain_expiry(domain):
    try:
        whois_url = f"https://whois.whoisxmlapi.com/api/v1?apiKey={WHOIS_API_KEY}&domainName={domain}"
        response = requests.get(whois_url)
        data = response.json()
        expiry_date = data['expiresDate']
        return datetime.strptime(expiry_date, '%Y-%m-%d')
    except Exception as e:
        print(f"Error checking {domain}: {e}")
        return None

def check_dns_records(domain):
    results = {
        'a_record': [],
        'cname': [],
        'mx': [],
        'txt': []
    }
    
    try:
        # Check A records
        answers = dns.resolver.resolve(domain, 'A')
        results['a_record'] = [str(rdata) for rdata in answers]
    except:
        pass

    try:
        # Check CNAME
        answers = dns.resolver.resolve(domain, 'CNAME')
        results['cname'] = [str(rdata) for rdata in answers]
    except:
        pass

    return results

def main():
    config = load_domain_config()
    expiring_domains = []
    
    for domain in config['domains']:
        expiry_date = check_domain_expiry(domain['name'])
        dns_records = check_dns_records(domain['name'])
        
        # Check if domain expires within 30 days
        if expiry_date and (expiry_date - datetime.now()).days < 30:
            expiring_domains.append({
                'domain': domain['name'],
                'expiration_date': expiry_date.strftime('%Y-%m-%d'),
                'dns_records': dns_records
            })
    
    # Save results
    if expiring_domains:
        with open('expiring_domains.json', 'w') as f:
            json.dump(expiring_domains, f)

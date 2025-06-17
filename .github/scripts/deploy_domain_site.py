#!/usr/bin/env python3
import os
import yaml
import shutil
import subprocess
from string import Template

def load_domain_config():
    with open('domain_config.yml', 'r') as file:
        return yaml.safe_load(file)

def prepare_site(domain):
    # Create directory for this domain
    domain_dir = f'sites/{domain["name"]}'
    os.makedirs(domain_dir, exist_ok=True)
    
    # Copy template files
    template_dir = 'templates/default'
    for file in os.listdir(template_dir):
        src = os.path.join(template_dir, file)
        dst = os.path.join(domain_dir, file)
        if os.path.isfile(src):
            with open(src, 'r') as f:
                content = f.read()
            
            # Replace placeholders
            content = content.replace('{{DOMAIN_NAME}}', domain['name'])
            
            with open(dst, 'w') as f:
                f.write(content)

def create_dockerfile(domain):
    dockerfile_content = '''FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]'''
    
    with open(f'sites/{domain["name"]}/Dockerfile', 'w') as f:
        f.write(dockerfile_content)

def deploy_to_cloud_run(domain):
    domain_dir = f'sites/{domain["name"]}'
    service_name = domain['cloud_run']['service_name']
    region = domain['cloud_run']['region']
    
    # Build container
    subprocess.run([
        'gcloud', 'builds', 'submit', domain_dir,
        '--tag', f'gcr.io/$PROJECT_ID/{service_name}'
    ])
    
    # Deploy to Cloud Run
    subprocess.run([
        'gcloud', 'run', 'deploy', service_name,
        '--image', f'gcr.io/$PROJECT_ID/{service_name}',
        '--platform', 'managed',
        '--region', region,
        '--allow-unauthenticated'
    ])
    
    # Map custom domain
    subprocess.run([
        'gcloud', 'beta', 'run', 'domain-mappings', 'create',
        '--service', service_name,
        '--domain', domain['name'],
        '--region', region
    ])

def main():
    config = load_domain_config()
    
    for domain in config['domains']:
        if domain.get('status') == 'active':
            print(f"Preparing site for {domain['name']}")
            prepare_site(domain)
            create_dockerfile(domain)
            print(f"Deploying {domain['name']} to Cloud Run")
            deploy_to_cloud_run(domain)

if __name__ == '__main__':
    main()

import os
import secrets

from tljh.hooks import hookimpl

@hookimpl
def tljh_custom_jupyterhub_config(c):
    internal_port = '18000'
    service_id = 'service-governedrun'
    client_secret = secrets.token_urlsafe(16)
    service_name = 'Governed-Run'
    url = os.environ.get('TLJH_BASE_URL', 'http://localhost')
    if url.endswith('/'):
        url = url[:-1]
    local_api_url = os.environ.get('TLJH_LOCAL_API_URL', 'http://localhost/hub/api')
    if local_api_url.endswith('/'):
        local_api_url = local_api_url[:-1]
    c.JupyterHub.services.append({
        'name': service_name,
        'admin': False,
        'command': [
            'uvicorn', 'governedrunner.main:app',
            '--host', '127.0.0.1', '--port', internal_port,
        ],
        'oauth_client_id': service_id,
        'api_token': client_secret,
        'oauth_redirect_uri': f'{url}/services/{service_name}/auth',
        'oauth_no_confirm': True,
        'environment': {
            'GOVERNEDRUNNER_BASE_PATH': f'/services/{service_name}',
            'OAUTH2_CLIENT_ID': service_id,
            'OAUTH2_CLIENT_SECRET': client_secret,
            'OAUTH2_TOKEN_URL': f'{local_api_url}/oauth2/token',
            'OAUTH2_AUTHORIZATION_URL': f'{url}/hub/api/oauth2/authorize',
            'USER_PROFILE_URL': f'{local_api_url}/user',
            'USER_PROFILE_PROPNAME': 'name',
            'DEBUG': os.environ.get('DEBUG', ''),
        },
        'url': f'http://127.0.0.1:{internal_port}',
    })

@hookimpl
def tljh_extra_hub_pip_packages():
    return [
        'fastapi',
        'fastapi-pagination',
        'starlette',
        'authlib',
        'httpx',
        'aiohttp-session',
        'itsdangerous',
        'uvicorn[standard]',
        'pydantic-settings',
        'python-multipart',
        'toml',
    ]

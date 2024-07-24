from starlette.requests import Request
from governedrunner.config import config

FORCE_HTTPS = config('FORCE_HTTPS', cast=bool, default=False)

def get_frontend_url(request: Request):
    url = request.url
    if not FORCE_HTTPS:
        return url
    return url.replace(scheme='https')

def get_frontend_base_url(request: Request):
    url = get_frontend_url(request)
    return f'{url.scheme}://{url.netloc}'

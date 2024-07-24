from starlette.requests import Request
from governedrunner.config import config

FORCE_HTTPS = config('FORCE_HTTPS', cast=bool, default=False)

def frontend_url_for(request: Request, name: str):
    url = request.url_for(name)
    if not FORCE_HTTPS:
        return url
    return url.replace(scheme='https')

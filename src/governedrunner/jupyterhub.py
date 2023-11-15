from tljh.hooks import hookimpl

@hookimpl
def tljh_custom_jupyterhub_config(c):
    c.JupyterHub.services.append({
        'name': 'Governed-Run',
        'admin': False,
    })

@hookimpl
def tljh_extra_hub_pip_packages():
    return [
        'fastapi',
        'fastapi-pagination',
        'uvicorn[standard]',
        'python-multipart',
        'toml',
    ]

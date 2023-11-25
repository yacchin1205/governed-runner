import os
import shutil
import subprocess
import tempfile
import yaml

from governedrunner.api import main

tools_path, _ = os.path.split(__file__)
ui_path, _ = os.path.split(tools_path)
root_path, _ = os.path.split(ui_path)
frontend_path = os.path.join(root_path, 'frontend')

if __name__ == '__main__':
    work_dir = tempfile.mkdtemp()
    try:
        openapi = main.app.openapi()
        openapi_path = os.path.join(work_dir, 'openapi.yml')
        with open(openapi_path, 'w') as f:
            yaml.dump(openapi, f, sort_keys=False)
        subprocess.check_call(
            [
                'npx',
                'openapi-typescript',
                openapi_path,
                '--output',
                os.path.join(frontend_path, 'app/api/schema.d.ts'),
            ],
        )
    finally:
        shutil.rmtree(work_dir)
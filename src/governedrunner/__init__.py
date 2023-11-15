import importlib.metadata
import toml

try:
    with open('pyproject.toml', 'rb') as f:
        pyproject = toml.load(f)
    __version__ = pyproject['project']['version']
except Exception as e:
    __version__ = importlib.metadata.version('governedrunner')

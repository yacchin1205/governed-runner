import logging
import importlib.metadata
import toml

logger = logging.getLogger(__name__)

try:
    from .jupyterhub import tljh_custom_jupyterhub_config, tljh_extra_hub_pip_packages
except ImportError:
    logger.warning('TLJH hooks not found, skipping...')

try:
    with open('pyproject.toml', 'rb') as f:
        pyproject = toml.load(f)
    __version__ = pyproject['project']['version']
except Exception as e:
    __version__ = importlib.metadata.version('governedrunner')

from typing import Optional
from pydantic_settings import BaseSettings
from traitlets.config import PyFileConfigLoader, Config


CRATE_FOLDER_NAME = '.crates'
DEFAULT_CONFIG_FILENAME = 'governedrunner_config.py'

class Settings(BaseSettings):
    demo_user: bool = False
    rdm_service_id: str = 'rdm.nii.ac.jp'
    rdm_web_url: str = 'https://rdm.nii.ac.jp'
    rdm_api_url: str = 'https://api.rdm.nii.ac.jp/v2'
    rdm_files_url: str = 'https://files.rdm.nii.ac.jp/v1'
    jupyterhub_config: Optional[str] = None

    _config: Config = None

    @property
    def jupyterhub_traitlets_config(self) -> Config:
        if self._config is not None:
            return self._config
        if self.jupyterhub_config is not None:
            loader = PyFileConfigLoader(self.jupyterhub_config)
        else:
            loader = PyFileConfigLoader(DEFAULT_CONFIG_FILENAME)
        self._config = loader.load_config()
        return self._config

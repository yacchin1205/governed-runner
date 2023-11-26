from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    demo_user: bool = False
    rdm_service_id: str = 'rdm.nii.ac.jp'
    rdm_api_url: str = 'https://api.rdm.nii.ac.jp/v2'
    rdm_files_url: str = 'https://files.rdm.nii.ac.jp/v1'

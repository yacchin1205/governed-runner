from fastapi import APIRouter

from governedrunner import __version__
from governedrunner.api.models import ServerOut


router = APIRouter()


@router.get('/', response_model=ServerOut)
def retrieve_server():
    '''
    このGoverned Runnerの情報です。
    '''
    return {
        'version': __version__,
    }

@router.get('/health', response_model=ServerOut)
def health_check():
    '''
    このGoverned Runnerのヘルスチェック用エンドポイントです。
    '''
    return {
        'version': __version__,
    }

from typing import Annotated

from fastapi import APIRouter, Depends

from governedrunner.api.auth import get_current_user
from governedrunner.api.models import UserOut
from governedrunner.db.models import User


router = APIRouter()


@router.get('/users/me', response_model=UserOut)
def retrieve_current_user(current_user: Annotated[User, Depends(get_current_user)]):
    '''
    指定された認証情報に対応するユーザーを取得します。
    '''
    return current_user

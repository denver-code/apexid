from fastapi import HTTPException, Header, Request
from app.core.validator import ValidatorError, ZitadelIntrospectTokenValidator
from pydantic import BaseModel
from typing import List, Optional


class AuthInfo(BaseModel):
    active: bool
    scope: str
    client_id: str
    token_type: str
    exp: int
    iat: int
    nbf: int
    sub: str
    aud: List[str]
    iss: str
    jti: str
    username: str
    name: Optional[str]
    given_name: Optional[str]
    family_name: Optional[str]
    nickname: str
    gender: Optional[str]
    locale: str
    updated_at: int
    preferred_username: Optional[str]
    email: str
    email_verified: bool


def auth_required(req: Request, authorization: str = Header("Authorization")):
    """Check if the user is authorized."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.split("Bearer ")[1]
    validator = ZitadelIntrospectTokenValidator()
    validator.validate_request(req)
    _token = validator.authenticate_token(token)

    try:
        validator.validate_token(_token, _token.get("scopes"), req)
        return _token
    except ValidatorError as e:
        raise HTTPException(status_code=e.status_code, detail=e.error)

from fastapi import HTTPException, status


def bearer_token(authorization: str | None) -> str:
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid sign-in session is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid sign-in session is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token.strip()

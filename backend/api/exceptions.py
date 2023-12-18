from fastapi import HTTPException, status

UNAUTHORIZE = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Unauthorize"
)

NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Not found"
)

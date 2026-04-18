from fastapi import HTTPException, status

class ValidationException(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

class NotFoundError(HTTPException):
    def __init__(self, resource: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} não encontrado"
        )

class PermissionDenied(HTTPException):
    def __init__(self, message: str = "Sem permissão para esta ação"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )

class DuplicateResourceError(HTTPException):
    def __init__(self, resource: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{resource} já existe"
        )

class AccountLockedError(HTTPException):
    def __init__(self, minutes: int = 15):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Conta bloqueada. Tente novamente em {minutes} minutos"
        )

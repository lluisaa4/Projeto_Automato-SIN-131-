class ValidationError(ValueError):
    """Erro de validacao das estruturas formais do sistema."""


class ParseError(ValidationError):
    """Erro de leitura de uma entrada textual informada pelo usuario."""

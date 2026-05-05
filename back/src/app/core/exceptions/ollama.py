class OllamaError(Exception):
    pass


class OllamaHTTPError(OllamaError):
    def __init__(self, status_code: int, endpoint: str, body: str = ''):
        self.status_code = status_code
        self.endpoint = endpoint
        self.body = body
        super().__init__(f'Ollama HTTP {status_code} at {endpoint}: {body[:200]}')

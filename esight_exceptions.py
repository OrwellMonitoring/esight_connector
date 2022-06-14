from http import HTTPStatus

class CouldNotLoginOnEsight(Exception):
    def __init__(self, username=None, password=None):
        self.status_code = HTTPStatus.UNAUTHORIZED
        if username and password:
            self.message = f'Could not login on eSight with userid "{username}" and value "{password}"'
        else:
            self.message = 'Could not get authentication token from eSIght using the provided credentials'
        super().__init__(self.message)

    def __str__(self):
        return self.message

class UnexpectedError(Exception):
    def __init__(self, msg):
        self.status_code = HTTPStatus.UNAUTHORIZED
        self.message = f'An unexpected error ocurred. Error Message: "{msg}"'
        super().__init__(self.message)

    def __str__(self):
        return self.message

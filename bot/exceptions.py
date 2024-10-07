

class MaplistResNotFound(Exception):
    def __init__(self, resource_name: str):
        super().__init__()
        self.resource_name = resource_name

    def formatted_exc(self) -> str:
        return f"Couldn't find the {self.resource_name} you're looking for!"


class ErrorStatusCode(Exception):
    def __init__(self, status_code: int):
        super().__init__()
        self.status_code = status_code

    def formatted_exc(self) -> str:
        return f"`[{self.status_code}]` Something weird happened!"


class BadRequest(Exception):
    def __init__(self, resp_json: dict):
        super().__init__()
        self.errors = resp_json["errors"]

    def formatted_exc(self) -> str:
        errors = []
        for key in self.errors:
            err = "- "
            if len(key):
                err += f"`{key}`: "
            err += self.errors[key]
            errors.append(err)
        return "\n".join(errors)

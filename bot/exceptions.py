import json


def stringify_errors(errors: dict[str, str]) -> str:
    str_errors = []
    for key in errors:
        err = ""
        if len(key):
            err += f"- `{key}`: "
        err += errors[key]
        str_errors.append(err)
    return "\n".join(str_errors)


class MaplistResNotFound(Exception):
    def __init__(self, resource_name: str):
        super().__init__()
        self.resource_name = resource_name

    def formatted_exc(self) -> str:
        return f"Couldn't find the {self.resource_name} you're looking for!"


class ErrorStatusCode(Exception):
    codes_to_str = {
        403: "You don't have the permissions to do this!",
        500: "Internal Server Error - Please take a screenshot & ping the bot owner, this is important!",
    }

    def __init__(self, status_code: int, errors: dict[str, str] = None):
        super().__init__()
        self.status_code = status_code
        self.errors = errors

    def formatted_exc(self) -> str:
        error = f"`[{self.status_code}]` Something weird happened!"
        if self.errors:
            error = ErrorStatusCode.codes_to_str.get(self.status_code, "") + "\n" + stringify_errors(self.errors)
        return error


class BadRequest(Exception):
    def __init__(self, resp_json: dict):
        super().__init__()
        self.resp_json = resp_json

    def formatted_exc(self) -> str:
        parts = []
        if "message" in self.resp_json:
            parts.append(self.resp_json["message"])
        if "errors" in self.resp_json:
            parts.append(stringify_errors(self.resp_json["errors"]))
        if not parts:
            parts.append(f"Something went wrong! Please take a screenshot & ping the bot owner.\n```json\n{json.dumps(self.resp_json, indent=2)}\n```")
        return "\n".join(parts)

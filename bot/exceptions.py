

class ExampleException(Exception):
    def formatted_exc(self) -> str:
        return "An example error was raised."

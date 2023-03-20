from json import load


def get_Credentials(service="onedrive"):
    with open("credentials.json", 'r') as credentials:
        credentials = load(credentials)

    return {
        f"{service}": credentials[service]
    }


class Metaclass(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Metaclass, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

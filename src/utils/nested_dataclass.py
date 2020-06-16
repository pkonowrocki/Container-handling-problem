from dataclasses import dataclass, is_dataclass


def nested_dataclass(*args, **kwargs):
    def wrapper(cls):
        cls = dataclass(cls, **kwargs)
        original_init = cls.__init__

        def __init__(self, *args, **kwargs):
            for name, value in kwargs.items():
                field_type = cls.__annotations__.get(name, None)
                if is_dataclass(field_type) and isinstance(value, dict):
                    new_obj = field_type(**value)
                    kwargs[name] = new_obj
                try:
                    if field_type.__origin__ == list:
                        if not isinstance(value, list):
                            value = [value]
                        elem_type = field_type.__args__[0]
                        new_obj = [elem_type(**item) for item in value]
                        kwargs[name] = new_obj
                except AttributeError:
                    pass
            original_init(self, *args, **kwargs)

        cls.__init__ = __init__
        return cls

    return wrapper(args[0]) if args else wrapper

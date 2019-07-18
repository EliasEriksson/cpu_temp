class _Base(Exception):
    def __init__(self, message):
        self.message = message


class ArgumentError(_Base):
    pass


class NothingToDo(_Base):
    pass

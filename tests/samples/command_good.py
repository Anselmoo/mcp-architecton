class PrintCommand:
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def execute(self) -> None:
        print(self.msg)


class Invoker:
    def __init__(self) -> None:
        self.queue: list[PrintCommand] = []

    def add(self, cmd: PrintCommand) -> None:
        self.queue.append(cmd)

    def run(self) -> None:
        for c in self.queue:
            c.execute()

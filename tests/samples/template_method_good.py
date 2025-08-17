class Base:
    def step1(self) -> str:
        return "1"

    def step2(self) -> str:
        return "2"

    def process(self) -> str:
        return self.step1() + self.step2()

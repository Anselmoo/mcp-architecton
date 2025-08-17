class UI:
    def show(self) -> str:
        svc = Service()
        return svc.fetch()


class Service:
    def fetch(self) -> str:
        repo = Repository()
        return repo.get()


class Repository:
    def get(self) -> str:
        return "ok"

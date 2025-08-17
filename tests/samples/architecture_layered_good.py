# Presentation layer
class Controller:
    def handle(self):
        svc = ApplicationService()
        return svc.do_something()


# Application layer
class ApplicationService:
    def do_something(self):
        repo = Repository()
        return repo.get_data()


# Domain layer
class DomainModel:
    pass


# Infrastructure layer
class Repository:
    def get_data(self):
        return "ok"

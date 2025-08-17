class ProductRepository:
    def __init__(self, session):
        self.session = session

    def add(self, product):
        self.session.add(product)

    def get(self, sku):
        return self.session.query("products").get(sku)

    def list(self):
        return self.session.query("products").all()

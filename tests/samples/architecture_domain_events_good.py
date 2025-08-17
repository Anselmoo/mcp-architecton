from dataclasses import dataclass


@dataclass
class Allocated:
    order_id: str
    sku: str


class Product:
    def __init__(self):
        self.events = []

    def allocate(self, order_id, sku):
        self.events.append(Allocated(order_id, sku))

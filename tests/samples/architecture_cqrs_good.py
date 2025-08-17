from dataclasses import dataclass


@dataclass
class CreateBatch:
    sku: str
    qty: int


@dataclass
class GetAvailable:
    sku: str


def handle_command(cmd, uow):
    # mutate state
    uow.products.add(cmd)


def handle_query(query, view):
    # read side
    return view.get_available(query.sku)

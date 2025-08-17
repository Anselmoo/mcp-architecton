handlers = {
    "Allocated": [lambda e, uow: None],
}


def handle(queue, uow):
    while queue:
        event = queue.pop(0)
        for h in handlers.get(event.__class__.__name__, []):
            h(event, uow)

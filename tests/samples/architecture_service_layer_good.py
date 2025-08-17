def allocate(order_id, sku, qty, uow):
    with uow as u:
        # find batch in repo and allocate
        product = u.products.get(sku)
        product.allocate(qty)
        u.commit()

from .cart import Cart


def cart(request):
    cart_obj = Cart(request)
    return {
        "cart_count": len(cart_obj),
        "cart_total": cart_obj.total_price(),
    }

from django.shortcuts import render


def offline_products(request):
    return render(request, "offline/products.html")


def offline_sales(request):
    return render(request, "offline/sales.html")


def offline_expenses(request):
    return render(request, "offline/expenses.html")


def offline_status(request):
    return render(request, "offline/status.html")

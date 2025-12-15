from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, F
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from .models import Category, Book, Author, Banner, FeaturedCategory


def home(request):
    categories = Category.objects.filter(parent__isnull=True)
    top_categories = categories[:4]
    authors = Author.objects.filter(is_featured=True)[:10]
    banners = Banner.objects.filter(is_active=True).order_by("order", "-created_at")[:5]
    featured_cfgs = FeaturedCategory.objects.filter(is_active=True).select_related("category")
    featured_sections = []
    for cfg in featured_cfgs:
        limit = cfg.limit or 10
        books = (
            Book.objects.filter(category=cfg.category)
            .select_related("author", "category")
            .order_by("-created_at")[:limit]
        )
        featured_sections.append(
            {
                "title": cfg.title or cfg.category.name,
                "category": cfg.category,
                "books": books,
            }
        )
    best_selling = Book.objects.select_related("author", "category").order_by("-views")[:6]
    new_books = Book.objects.select_related("author", "category").order_by("-created_at")[:6]
    recommended = (
        Book.objects.filter(is_recommended=True)
        .select_related("author", "category")
        .order_by("-created_at")[:6]
    )
    return render(
        request,
        "home.html",
        {
            "categories": top_categories,
            "authors": authors,
            "banners": banners,
            "featured_sections": featured_sections,
            "best_selling": best_selling,
            "new_books": new_books,
            "recommended": recommended,
        },
    )


def categories_list(request):
    categories = Category.objects.filter(parent__isnull=True).order_by("name")
    return render(request, "categories_list.html", {"categories": categories})


def authors_list(request):
    authors = Author.objects.all().order_by("name")
    return render(request, "authors_list.html", {"authors": authors})


def about(request):
    from .models import AboutPage

    about_page = (
        AboutPage.objects.filter(is_active=True)
        .order_by("-updated_at", "-id")
        .first()
    )
    return render(request, "about.html", {"about_page": about_page})


def new_books_list(request):
    books = Book.objects.order_by("-created_at")
    return render(request, "book_list.html", {"title": "Yangi qo‘shilganlar", "books": books})


def best_selling_list(request):
    books = Book.objects.order_by("-views")
    return render(request, "book_list.html", {"title": "Eng ko‘p sotilganlar", "books": books})


def recommended_list(request):
    books = Book.objects.filter(is_recommended=True).order_by("-created_at")
    return render(request, "book_list.html", {"title": "Tavsiya etilganlar", "books": books})


def author_detail(request, author_id):
    author = get_object_or_404(Author, id=author_id)
    books = Book.objects.filter(author=author).select_related("category").order_by("-created_at")
    return render(request, "book_list.html", {"title": author.name, "books": books})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    descendants = category.children.all()
    books = (
        Book.objects.filter(category__in=[category] + list(descendants))
        .select_related("author", "category")
    )
    authors = Author.objects.filter(books__category=category).distinct()
    if descendants.exists():
        authors = Author.objects.filter(books__category__in=[category] + list(descendants)).distinct()

    author_id = request.GET.get("author")
    if author_id:
        books = books.filter(author_id=author_id)

    sort = request.GET.get("sort")
    sort_map = {
        "price_asc": "sale_price",
        "price_desc": "-sale_price",
        "newest": "-created_at",
        "oldest": "created_at",
        "popular": "-views",
    }
    if sort in sort_map:
        books = books.order_by(sort_map[sort])

    return render(
        request,
        "category_list.html",
        {
            "category": category,
            "books": books,
            "authors": authors,
            "current_author": author_id,
            "current_sort": sort,
            "child_categories": descendants,
        },
    )


def book_detail(request, id, slug):
    book = get_object_or_404(Book.objects.select_related("author", "category"), id=id, slug=slug)
    Book.objects.filter(id=book.id).update(views=F("views") + 1)
    favorites = request.session.get("favorites", [])
    in_favorites = str(book.id) in favorites
    return render(request, "book_detail.html", {"book": book, "in_favorites": in_favorites})


def search(request):
    def normalize(v):
        return None if v in [None, "", "None", "null"] else v

    query = request.GET.get("q", "").strip()

    # Normalize GET params
    author_id = normalize(request.GET.get("author"))
    category_slug = normalize(request.GET.get("category"))
    sort = normalize(request.GET.get("sort"))
    limit = normalize(request.GET.get("limit"))

    books = Book.objects.none()
    authors = Author.objects.none()
    categories = Category.objects.all()

    sort_options = [
        ("", "Mosligi bo‘yicha"),
        ("popular", "Eng saralar"),
        ("newest", "Yangi"),
        ("alpha_asc", "Alifbo (A-Z)"),
        ("alpha_desc", "Alifbo (Z-A)"),
        ("price_desc", "Narx (qimmat-arzon)"),
        ("price_asc", "Narx (arzon-qimmat)"),
    ]

    limit_options = ["8", "12", "16", "24", "32"]

    if query:
        books = Book.objects.filter(
            Q(title__icontains=query)
            | Q(author__name__icontains=query)
            | Q(category__name__icontains=query)
        ).select_related("author", "category")

        # Filter by author
        if author_id:
            books = books.filter(author_id=author_id)

        # Filter by category
        if category_slug:
            books = books.filter(category__slug=category_slug)

        # Sorting
        sort_map = {
            "price_asc": "sale_price",
            "price_desc": "-sale_price",
            "newest": "-created_at",
            "oldest": "created_at",
            "popular": "-views",
            "alpha_asc": "title",
            "alpha_desc": "-title",
        }

        if sort in sort_map:
            books = books.order_by(sort_map[sort])

        # Sidebar authors
        authors = Author.objects.filter(books__in=books).distinct()

        # Limit
        if limit:
            try:
                limit_int = int(limit)
                if limit_int > 0:
                    books = books[:limit_int]
            except ValueError:
                pass

    return render(
        request,
        "search_results.html",
        {
            "query": query,
            "books": books,
            "authors": authors,
            "categories": categories,
            "current_author": author_id,
            "current_category": category_slug,
            "current_sort": sort,
            "current_limit": limit,
            "sort_options": sort_options,
            "limit_options": limit_options,
        },
    )



def favorites(request):
    fav_ids = request.session.get("favorites", [])
    books = Book.objects.filter(id__in=fav_ids).select_related("author", "category")
    return render(request, "favorites.html", {"books": books})


def add_favorite(request, book_id):
    favs = request.session.get("favorites", [])
    key = str(book_id)
    if key not in favs:
        favs.append(key)
    request.session["favorites"] = favs
    request.session.modified = True
    referer = request.META.get("HTTP_REFERER")
    if referer and url_has_allowed_host_and_scheme(referer, allowed_hosts={request.get_host()}):
        return redirect(referer)
    return redirect("favorites")


def remove_favorite(request, book_id):
    favs = request.session.get("favorites", [])
    key = str(book_id)
    if key in favs:
        favs.remove(key)
        request.session["favorites"] = favs
        request.session.modified = True
    referer = request.META.get("HTTP_REFERER")
    if referer and url_has_allowed_host_and_scheme(referer, allowed_hosts={request.get_host()}):
        return redirect(referer)
    return redirect("favorites")

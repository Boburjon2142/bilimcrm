from django.contrib.admin.views.decorators import staff_member_required
from django.forms import modelform_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from apps.catalog.models import AboutPage, Author, Banner, Book, Category, FeaturedCategory
from apps.crm.models import Courier, Customer, Debt, Expense, InventoryLog
from apps.orders.models import DeliveryNotice, DeliverySettings, DeliveryZone, Order, OrderItem


ALLOWED_MODELS = {
    "catalog": [Author, Category, FeaturedCategory, Book, Banner, AboutPage],
    "crm": [Customer, Courier, InventoryLog, Expense, Debt],
    "orders": [Order, OrderItem, DeliveryZone, DeliveryNotice, DeliverySettings],
}


def _model_map():
    model_map = {}
    for app_label, models in ALLOWED_MODELS.items():
        model_map[app_label] = {}
        for model in models:
            model_map[app_label][model._meta.model_name] = model
    return model_map


def _get_model(app_label: str, model_name: str):
    model_map = _model_map()
    model = model_map.get(app_label, {}).get(model_name)
    if not model:
        raise Http404("Model not found.")
    return model


def _form_class(model):
    fields = [f.name for f in model._meta.fields if f.editable and not f.auto_created]
    fields += [m.name for m in model._meta.many_to_many if m.editable]
    return modelform_factory(model, fields=fields)


def _style_form(form):
    for field in form.fields.values():
        widget = field.widget
        if widget.__class__.__name__ in {"CheckboxInput", "RadioSelect"}:
            continue
        existing = widget.attrs.get("class", "")
        widget.attrs["class"] = (existing + " form-control").strip()
    return form


@staff_member_required
def admin_index(request):
    model_map = _model_map()
    sections = []
    for app_label, models in model_map.items():
        items = []
        for model_name, model in models.items():
            items.append(
                {
                    "name": model._meta.verbose_name_plural.title(),
                    "model_name": model_name,
                    "app_label": app_label,
                }
            )
        sections.append({"app_label": app_label, "items": items})
    return render(request, "crm/admin/index.html", {"sections": sections})


@staff_member_required
def admin_list(request, app_label: str, model_name: str):
    model = _get_model(app_label, model_name)
    objects = model.objects.order_by("-id")[:500]
    fields = [f for f in model._meta.fields if f.name not in {"id"}][:6]
    return render(
        request,
        "crm/admin/list.html",
        {
            "model": model,
            "objects": objects,
            "fields": fields,
            "app_label": app_label,
            "model_name": model_name,
        },
    )


@staff_member_required
def admin_create(request, app_label: str, model_name: str):
    model = _get_model(app_label, model_name)
    form_class = _form_class(model)
    form = form_class(request.POST or None, request.FILES or None)
    _style_form(form)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("crm_admin_list", app_label=app_label, model_name=model_name)
    return render(
        request,
        "crm/admin/form.html",
        {
            "form": form,
            "model": model,
            "app_label": app_label,
            "model_name": model_name,
            "is_edit": False,
        },
    )


@staff_member_required
def admin_update(request, app_label: str, model_name: str, pk: int):
    model = _get_model(app_label, model_name)
    instance = get_object_or_404(model, pk=pk)
    form_class = _form_class(model)
    form = form_class(request.POST or None, request.FILES or None, instance=instance)
    _style_form(form)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("crm_admin_list", app_label=app_label, model_name=model_name)
    return render(
        request,
        "crm/admin/form.html",
        {
            "form": form,
            "model": model,
            "app_label": app_label,
            "model_name": model_name,
            "is_edit": True,
            "object": instance,
        },
    )


@staff_member_required
def admin_delete(request, app_label: str, model_name: str, pk: int):
    model = _get_model(app_label, model_name)
    instance = get_object_or_404(model, pk=pk)
    if request.method == "POST":
        instance.delete()
        return redirect("crm_admin_list", app_label=app_label, model_name=model_name)
    return render(
        request,
        "crm/admin/delete.html",
        {
            "model": model,
            "object": instance,
            "app_label": app_label,
            "model_name": model_name,
        },
    )

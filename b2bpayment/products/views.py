from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from core.mixins import TenantRequiredMixin
from .models import Product
from .forms import ProductForm

class ProductListView(TenantRequiredMixin, ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        search_query = self.request.GET.get('q', '').strip()
        stock_filter = self.request.GET.get('stock', '').strip()

        if search_query:
            qs = qs.filter(Q(name__icontains=search_query) | Q(sku__icontains=search_query) | Q(category__icontains=search_query))
        
        if stock_filter == 'low':
            qs = [p for p in qs if p.is_low_stock]
        elif stock_filter == 'out':
            qs = [p for p in qs if p.is_out_of_stock]
        elif stock_filter == 'in':
            qs = [p for p in qs if p.stock_quantity > p.low_stock_threshold]

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_products = Product.objects.filter(business=self.request.business)
        context['total_products'] = all_products.count()
        context['low_stock_count'] = sum(1 for p in all_products if p.is_low_stock)
        context['out_of_stock_count'] = sum(1 for p in all_products if p.is_out_of_stock)
        context['search_query'] = self.request.GET.get('q', '')
        context['stock_filter'] = self.request.GET.get('stock', '')
        return context

class ProductCreateView(TenantRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:list')

    def form_valid(self, form):
        form.instance.business = self.request.business
        messages.success(self.request, f"Product '{form.instance.name}' added to inventory!")
        return super().form_valid(form)

class ProductUpdateView(TenantRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:list')

    def form_valid(self, form):
        messages.success(self.request, "Product updated successfully!")
        return super().form_valid(form)

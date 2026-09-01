from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q

from core.mixins import TenantRequiredMixin
from customers.models import Customer
from whatsapp.models import WhatsAppConversation, WhatsAppMessage
from .models import Promotion, PromotionImage
from .forms import PromotionForm, PromotionImageForm

class PromotionListView(TenantRequiredMixin, View):
    def get(self, request):
        business = request.business
        promotions = Promotion.objects.filter(business=business)

        q = request.GET.get('q', '').strip()
        if q:
            promotions = promotions.filter(
                Q(name__icontains=q) |
                Q(title__icontains=q) |
                Q(message__icontains=q)
            )

        return render(request, 'promotions/promotion_list.html', {
            'promotions': promotions,
            'q': q
        })

class PromotionDetailView(TenantRequiredMixin, View):
    def get(self, request, pk):
        promotion = get_object_or_404(Promotion, pk=pk, business=request.business)
        images = promotion.images.all()
        can_upload = promotion.can_upload_more_images

        return render(request, 'promotions/promotion_detail.html', {
            'promotion': promotion,
            'images': images,
            'can_upload': can_upload
        })

class PromotionCreateView(TenantRequiredMixin, View):
    def get(self, request):
        form = PromotionForm()
        return render(request, 'promotions/promotion_form.html', {
            'form': form,
            'title': 'Create New Promotion'
        })

    def post(self, request):
        business = request.business
        form = PromotionForm(request.POST)
        if form.is_valid():
            promotion = form.save(commit=False)
            promotion.business = business
            promotion.save()

            # Process optional image uploads (max 2)
            files = request.FILES.getlist('images')
            for f in files[:2]:
                PromotionImage.objects.create(
                    business=business,
                    promotion=promotion,
                    image=f
                )

            messages.success(request, f"Promotion '{promotion.name}' created successfully!")
            return redirect('promotions:detail', pk=promotion.pk)

        return render(request, 'promotions/promotion_form.html', {
            'form': form,
            'title': 'Create New Promotion'
        })

class PromotionUpdateView(TenantRequiredMixin, View):
    def get(self, request, pk):
        promotion = get_object_or_404(Promotion, pk=pk, business=request.business)
        form = PromotionForm(instance=promotion)
        return render(request, 'promotions/promotion_form.html', {
            'form': form,
            'promotion': promotion,
            'title': f'Edit Promotion: {promotion.name}'
        })

    def post(self, request, pk):
        business = request.business
        promotion = get_object_or_404(Promotion, pk=pk, business=business)
        form = PromotionForm(request.POST, instance=promotion)
        if form.is_valid():
            form.save()

            # Upload additional poster images if count < 2
            if promotion.can_upload_more_images:
                files = request.FILES.getlist('images')
                remaining_slots = 2 - promotion.images.count()
                for f in files[:remaining_slots]:
                    PromotionImage.objects.create(
                        business=business,
                        promotion=promotion,
                        image=f
                    )

            messages.success(request, f"Promotion '{promotion.name}' updated!")
            return redirect('promotions:detail', pk=promotion.pk)

        return render(request, 'promotions/promotion_form.html', {
            'form': form,
            'promotion': promotion,
            'title': f'Edit Promotion: {promotion.name}'
        })

class PromotionDeleteView(TenantRequiredMixin, View):
    def get(self, request, pk):
        promotion = get_object_or_404(Promotion, pk=pk, business=request.business)
        return render(request, 'promotions/promotion_delete.html', {'promotion': promotion})

    def post(self, request, pk):
        promotion = get_object_or_404(Promotion, pk=pk, business=request.business)
        name = promotion.name
        promotion.delete()
        messages.success(request, f"Promotion '{name}' deleted.")
        return redirect('promotions:list')

class PromotionImageDeleteView(TenantRequiredMixin, View):
    def post(self, request, pk):
        image_obj = get_object_or_404(PromotionImage, pk=pk, business=request.business)
        promo_pk = image_obj.promotion.pk
        image_obj.delete()
        messages.success(request, "Poster image deleted. You can now upload a replacement poster.")
        return redirect('promotions:detail', pk=promo_pk)

class PromotionSendView(TenantRequiredMixin, View):
    def get(self, request, pk):
        business = request.business
        promotion = get_object_or_404(Promotion, pk=pk, business=business)
        customers = Customer.objects.filter(business=business)
        images = promotion.images.all()

        target_customer_id = request.GET.get('customer_id')
        selected_customer = Customer.objects.filter(pk=target_customer_id, business=business).first() if target_customer_id else None

        return render(request, 'promotions/promotion_send.html', {
            'promotion': promotion,
            'customers': customers,
            'selected_customer': selected_customer,
            'images': images
        })

    def post(self, request, pk):
        business = request.business
        promotion = get_object_or_404(Promotion, pk=pk, business=business)
        images = promotion.images.all()

        customer_ids = request.POST.getlist('customer_ids')
        if not customer_ids:
            # Fallback to single customer select
            single_cust = request.POST.get('customer_id')
            if single_cust:
                customer_ids = [single_cust]

        selected_customers = Customer.objects.filter(pk__in=customer_ids, business=business)

        sent_count = 0
        for customer in selected_customers:
            if not customer.phone:
                continue

            # Ensure conversation exists
            conv, _ = WhatsAppConversation.objects.get_or_create(
                business=business,
                customer=customer
            )

            # Build full message text
            full_msg_text = f"*{promotion.title}*\n\n{promotion.message}"

            # Log main text message
            WhatsAppMessage.objects.create(
                conversation=conv,
                sender='business',
                message_text=full_msg_text,
                status='Sent'
            )

            sent_count += 1

        messages.success(request, f"🎉 Promotion '{promotion.name}' successfully sent via WhatsApp to {sent_count} customer(s)!")
        return redirect('promotions:detail', pk=promotion.pk)

from django.core.management.base import BaseCommand
from products.models import Product
from products.saas_registry import SAAS_PRODUCTS


class Command(BaseCommand):
    help = "Synchronize registered SaaS products into the Product database table."

    def handle(self, *args, **options):
        count = 0
        for slug, item in SAAS_PRODUCTS.items():
            product, created = Product.objects.update_or_create(
                name=item["name"],
                defaults={
                    "description": item["description"],
                    "category": item["category_code"],
                    "price_inr_monthly": item["price_inr_monthly"],
                    "price_inr_yearly": item["price_inr_yearly"],
                    "price_usd_monthly": item["price_usd_monthly"],
                    "price_usd_yearly": item["price_usd_yearly"],
                    "features": "\n".join([f"{f['title']}: {f['desc']}" for f in item.get("features", [])]),
                    "access_info": f"Launch URL: /products/saas/{item['slug']}/launch/",
                    "is_active": (item.get("status", "active") == "active"),
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} product: {product.name}"))
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully synchronized {count} SaaS products."))

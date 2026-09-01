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
                    "price": item["price"],
                    "billing_type": item["billing_type"],
                    "features": f"Category: {item['category']}\nProject: {item['project_name']}\nStatus: {item['status']}",
                    "access_info": f"Launch URL: /products/saas/{item['slug']}/launch/",
                    "is_active": (item["status"] == "active"),
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} product: {product.name}"))
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully synchronized {count} SaaS products."))

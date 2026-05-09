from django.core.management.base import BaseCommand
from migration.models import LegacyOrder
import json
import random

class Command(BaseCommand):
    help = 'Seeds the database with legacy data'

    def handle(self, *args, **options):
        total_records = 500000
        batch_size = 10000
        
        self.stdout.write(f"Seeding {total_records} legacy records...")
        
        for i in range(0, total_records, batch_size):
            batch = []
            for j in range(i, min(i + batch_size, total_records)):
                external_id = f"legacy-{j}"
                raw_data = {
                    "customer_email": f"customer_{j}@example.com",
                    "total": str(round(random.uniform(10.0, 500.0), 2)),
                    "items": [
                        {"sku": f"SKU-{random.randint(1, 100)}", "quantity": random.randint(1, 5), "unit_price": str(round(random.uniform(5.0, 50.0), 2))},
                        {"sku": f"SKU-{random.randint(1, 100)}", "quantity": random.randint(1, 5), "unit_price": str(round(random.uniform(5.0, 50.0), 2))}
                    ]
                }
                batch.append(LegacyOrder(
                    external_id=external_id,
                    raw_data=raw_data,
                    migrated=False
                ))
            
            LegacyOrder.objects.bulk_create(batch)
            self.stdout.write(f"Created {min(i + batch_size, total_records)} / {total_records} records")
            
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {total_records} records'))

import time
import tracemalloc
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from migration.models import LegacyOrder, Order, OrderLine

class Command(BaseCommand):
    help = 'Migrates legacy orders to the new schema'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=1000, help='Number of records to process in a single batch')
        parser.add_argument('--dry-run', action='store_true', help='Simulate the migration without writing to the database')
        parser.add_argument('--start-from', type=str, help='external_id from which to begin the migration')

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        start_from = options['start_from']

        queryset = LegacyOrder.objects.filter(migrated=False).order_by('external_id')
        if start_from:
            queryset = queryset.filter(external_id__gte=start_from)

        total_to_process = queryset.count()
        if total_to_process == 0:
            self.stdout.write(self.style.SUCCESS("No records to migrate."))
            return

        self.stdout.write(f"Starting migration of {total_to_process} records...")
        if dry_run:
            self.stdout.write(self.style.WARNING("[Dry Run] No changes will be saved."))

        start_time = time.perf_counter()
        tracemalloc.start()

        orders_to_create = []
        lines_to_create = []
        processed_ids = []
        
        processed_count = 0

        try:
            for legacy_order in queryset.iterator(chunk_size=batch_size):
                # 1. Transform raw_data into Order and OrderLine instances
                raw_data = legacy_order.raw_data
                new_order = Order(
                    customer_email=raw_data['customer_email'],
                    total_price=raw_data['total'],
                    external_id=legacy_order.external_id
                )
                orders_to_create.append(new_order)
                
                for item in raw_data['items']:
                    new_line = OrderLine(
                        sku=item['sku'],
                        quantity=item['quantity'],
                        unit_price=item['unit_price']
                    )
                    # Temporarily store external_id on the order line object to link later
                    new_line._temp_external_id = legacy_order.external_id
                    lines_to_create.append(new_line)
                
                processed_ids.append(legacy_order.id)

                # 3. When a batch is full, process it
                if len(orders_to_create) >= batch_size:
                    self.process_batch(orders_to_create, lines_to_create, processed_ids, options)
                    processed_count += len(orders_to_create)
                    self.stdout.write(f"Successfully processed batch of {len(orders_to_create)} records.")
                    orders_to_create = []
                    lines_to_create = []
                    processed_ids = []

            # 4. Process any remaining records in the last partial batch
            if orders_to_create:
                self.process_batch(orders_to_create, lines_to_create, processed_ids, options)
                processed_count += len(orders_to_create)
                self.stdout.write(f"Successfully processed batch of {len(orders_to_create)} records.")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Migration failed: {str(e)}"))
            raise e

        end_time = time.perf_counter()
        duration = end_time - start_time
        throughput = processed_count / duration if duration > 0 else 0
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.stdout.write("\n" + "="*30)
        self.stdout.write(self.style.SUCCESS("Migration Completed!"))
        self.stdout.write(f"Total time: {duration:.2f} seconds")
        self.stdout.write(f"Throughput: {throughput:.2f} records per second")
        self.stdout.write(f"Peak memory usage: {peak / 10**6:.2f} MB")
        self.stdout.write("="*30)

    def process_batch(self, orders, lines, legacy_ids, options):
        if options['dry_run']:
            self.stdout.write(f"[Dry Run] Would process {len(orders)} records.")
            return

        try:
            with transaction.atomic():
                # Step 1: Create Orders
                Order.objects.bulk_create(orders)
                
                # Re-fetch created orders to get their PKs (required for ForeignKeys)
                # This is tricky because bulk_create doesn't return PKs on all DBs.
                # Common pattern: fetch by unique natural key.
                created_orders = Order.objects.filter(
                    external_id__in=[o.external_id for o in orders]
                ).in_bulk(field_name='external_id')
                
                # Step 2: Associate OrderLines with their new parent Orders
                for line in lines:
                    line.order = created_orders[line._temp_external_id]
                
                # Step 3: Create OrderLines
                OrderLine.objects.bulk_create(lines)
                
                # Step 4: Mark legacy orders as migrated
                LegacyOrder.objects.filter(id__in=legacy_ids).update(migrated=True)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
            raise e

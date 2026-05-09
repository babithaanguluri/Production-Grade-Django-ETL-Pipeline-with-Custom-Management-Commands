# Django ETL Pipeline - Large-Scale Data Migration

A robust, memory-efficient, and resumable data migration pipeline built with Django. This project demonstrates advanced ORM techniques for handling 500,000+ records in a production-grade environment.

##  Features
- **Memory Efficient**: Uses `queryset.iterator()` to process millions of records with a constant memory footprint.
- **High Performance**: Leverages `bulk_create()` for batch insertions, reducing database round-trips.
- **Idempotent & Resumable**: Safely resume interrupted migrations without creating duplicate data.
- **Transactional Safety**: Atomic batch processing ensures data consistency even in case of failure.
- **Fully Containerized**: Ready-to-use Docker and Docker Compose setup with PostgreSQL.

##  Quick Start

Follow these commands in order to demonstrate the full ETL pipeline:

1. **Start Services**:
   ```bash
   docker-compose up --build -d
   ```
2. **Apply Database Schema**:
   ```bash
   docker-compose exec app python manage.py migrate
   ```
3. **Seed Legacy Data (500k Records)**:
   ```bash
   docker-compose exec app python manage.py seed_legacy_data
   ```
4. **Run Dry Run Migration**:
   ```bash
   docker-compose exec app python manage.py migrate_orders --dry-run
   ```
5. **Execute Full Migration**:
   ```bash
   docker-compose exec app python manage.py migrate_orders --batch-size 5000
   ```
6. **Verify Idempotency**:
   ```bash
   docker-compose exec app python manage.py migrate_orders --batch-size 5000
   ```

##  Benchmarks
Detailed performance and memory profiling results can be found in [benchmark.md](./benchmark.md).

### Summary Comparison
| Metric | Naive Approach | Optimized (Bulk) |
| :--- | :--- | :--- |
| **Queries for 1k Records** | 4,001 | ~6 |
| **Memory (500k Records)** | OOM (>2GB) | ~15MB (Constant) |
| **Execution Speed** | Very Slow | High Throughput |

##  Architecture
- **LegacyOrder**: Denormalized source table containing raw JSON data.
- **Order & OrderLine**: Normalized destination tables.
- **Atomic Batches**: The system re-fetches created primary keys using a unique natural key (`external_id`) to correctly link order lines during bulk insertion.

##  License
MIT
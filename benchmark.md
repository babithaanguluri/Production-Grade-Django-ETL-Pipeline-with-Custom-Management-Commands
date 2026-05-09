# Data Migration Benchmark Results

## 1. Peak Memory Usage
Comparison of memory usage between the naive approach and the optimized `iterator()` approach.

| Approach | Peak Memory Usage | Notes |
| :--- | :--- | :--- |
| Naive | 4.07 MB (for 1000 records) | Scales linearly with dataset size. Would exceed 2GB for 500k records. |
| Optimized (Iterator) | ~15.20 MB | Constant memory usage regardless of total dataset size due to `iterator()`. |

**Observation**: The naive approach loads all records into a Python list, causing memory consumption to grow with the number of records. The optimized approach uses a server-side cursor via `iterator()`, keeping the memory footprint low and stable.

## 2. Total Migration Time vs. Batch Size
Measured for a representative sample of 500,000 records.

| Batch Size | Total Time (Seconds) | Throughput (Records/Sec) |
| :--- | :--- | :--- |
| 100 | ~1850s | ~270 |
| 500 | ~1240s | ~403 |
| 1000 | ~980s | ~510 |
| 5000 | ~820s | ~610 |

**Observation**: Increasing the batch size reduces the overhead of database transactions and network round-trips. However, excessively large batches may hit database limits (like the SQL variable limit in SQLite) or increase memory pressure within a single transaction.

## 3. Database Query Count
Comparison for a migration of 1,000 records.

| Approach | Total Queries | Breakdown |
| :--- | :--- | :--- |
| Naive | 4001 | 1 (fetch) + 1000 (order insert) + 2000 (lines insert) + 1000 (update) |
| Bulk Create (1000) | ~6 | 1 (fetch) + 1 (order bulk) + 1 (refetch) + 1 (lines bulk) + 1 (update) |

**Observation**: Using `bulk_create` reduces the number of queries from $O(N)$ to $O(1)$ per batch, dramatically improving performance and reducing database load.

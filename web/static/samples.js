/* Sample snippets — each one chosen to trip a different part of the analyser:
   recursion and memoisation, nested loops with a super-linear call inside, a
   swallowed exception, a cross join, manual memory. */
window.SAMPLES = {
  python: `from functools import lru_cache


class RouteCache:
    """Remembers the cheapest path between two stops."""

    def __init__(self, graph, capacity=128):
        self.graph = graph
        self.capacity = capacity
        self._hits = 0

    def cheapest(self, start, end):
        seen = {start: 0}
        frontier = [(0, start)]
        while frontier:
            cost, node = min(frontier)
            frontier.remove((cost, node))
            if node == end:
                return cost
            for neighbour, weight in self.graph[node].items():
                if neighbour not in seen or cost + weight < seen[neighbour]:
                    seen[neighbour] = cost + weight
                    frontier.append((cost + weight, neighbour))
        return None


@lru_cache(maxsize=None)
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)


def duplicate_pairs(items, others=[]):
    found = []
    for a in items:
        for b in others:
            if a == b:
                found.append(sorted((a, b)))
    return found


def load(path):
    try:
        with open(path) as handle:
            return handle.read()
    except:
        pass
`,

  javascript: `import { readFile } from 'node:fs/promises';

export class RateLimiter extends EventEmitter {
  #buckets = new Map();

  constructor(limit = 60, windowMs = 60_000) {
    super();
    this.limit = limit;
    this.windowMs = windowMs;
  }

  async allow(key) {
    const now = Date.now();
    const bucket = this.#buckets.get(key) ?? [];
    while (bucket.length && now - bucket[0] > this.windowMs) {
      bucket.shift();
    }
    if (bucket.length >= this.limit) {
      this.emit('throttled', { key, retryIn: this.windowMs });
      return false;
    }
    bucket.push(now);
    this.#buckets.set(key, bucket);
    return true;
  }
}

const slugify = (title) => title.toLowerCase().replace(/[^a-z0-9]+/g, '-');

async function loadAll(paths) {
  const results = [];
  for (const path of paths) {
    for (const other of paths) {
      if (path !== other && path.endsWith(other)) {
        results.push(\`\${path} shadows \${other}\`);
      }
    }
  }
  try {
    return await Promise.all(paths.map((p) => readFile(p, 'utf8')));
  } catch (error) {
    throw new Error('could not read inputs');
  } finally {
    results.length = 0;
  }
}
`,

  java: `package com.example.routing;

import java.util.HashMap;
import java.util.Map;

public class PathFinder implements Runnable {
    private final Map<String, Integer> cache = new HashMap<>();
    private final int maxDepth;

    public PathFinder(int maxDepth) {
        this.maxDepth = maxDepth;
    }

    @Override
    public void run() {
        System.out.println("searching to depth " + maxDepth);
    }

    public int fib(int n) {
        if (n <= 1) return n;
        return fib(n - 1) + fib(n - 2);
    }

    public int countCollisions(String[] left, String[] right) {
        int total = 0;
        for (int i = 0; i < left.length; i++) {
            for (String candidate : right) {
                if (left[i].equals(candidate)) {
                    total++;
                }
            }
        }
        return total;
    }

    void risky() {
        try {
            run();
        } catch (RuntimeException error) {
            throw new IllegalStateException(error);
        } finally {
            cache.clear();
        }
    }
}
`,

  cpp: `#include <vector>
#include <unordered_map>
#include <iostream>

namespace routing {

template <typename T>
class Graph {
 public:
  explicit Graph(int capacity) : capacity_(capacity) {
    buffer_ = new T[capacity];
  }

  ~Graph() { delete[] buffer_; }

  int fib(int n) const {
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);
  }

  int collisions(const std::vector<T>& left, const std::vector<T>& right) {
    int total = 0;
    for (size_t i = 0; i < left.size(); ++i) {
      for (const auto& candidate : right) {
        if (left[i] == candidate) {
          ++total;
        }
      }
    }
    return total;
  }

  void report() {
    auto emit = [&](const T& value) { std::cout << value << "\\n"; };
    for (const auto& entry : index_) {
      emit(entry.second);
    }
  }

 private:
  int capacity_;
  T* buffer_;
  std::unordered_map<int, T> index_;
};

}  // namespace routing
`,

  sql: `WITH recent_orders AS (
  SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_cents) AS lifetime_cents
  FROM orders
  WHERE created_at > '2026-01-01'
  GROUP BY customer_id
  HAVING COUNT(*) > 3
)

SELECT
  c.name,
  c.country,
  r.order_count,
  r.lifetime_cents / 100.0 AS lifetime_value,
  ROW_NUMBER() OVER (PARTITION BY c.country ORDER BY r.lifetime_cents DESC) AS rank_in_country
FROM customers c
JOIN recent_orders r ON r.customer_id = c.id
LEFT JOIN refunds f ON f.customer_id = c.id
CROSS JOIN exchange_rates e
WHERE c.active = TRUE
ORDER BY r.lifetime_cents DESC
LIMIT 50;
`,
};

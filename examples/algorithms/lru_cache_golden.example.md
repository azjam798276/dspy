---
id: "lru_cache_golden"
source_story: "stories/algorithms/lru_cache_eviction.story.md"
tags: ["algorithm", "cache", "hashmap", "doubly-linked-list"]
---

## Problem

Implement LRU Cache with O(1) get/put operations.
- Capacity: 2 (for testing)
- Evict Least Recently Used item when full
- get(key): O(1), return -1 if not found
- put(key, value): O(1), evict if over capacity

## Solution

// path: src/algorithms/lruCache.js
class LRUCache {
constructor(capacity) {
this.capacity = capacity;
this.cache = new Map(); // key -> Node
this.head = { key: null, val: null, prev: null, next: null };
this.tail = { key: null, val: null, prev: null, next: null };
this.head.next = this.tail;
this.tail.prev = this.head;
}

get(key) {
const node = this.cache.get(key);
if (!node) return -1;

text
// Move to front (most recently used)
this._detach(node);
this._attach(node);
return node.val;
}

put(key, value) {
let node = this.cache.get(key);

text
if (node) {
  // Update value and move to front
  node.val = value;
  this._detach(node);
  this._attach(node);
} else {
  // Create new node
  node = { key, val: value, prev: null, next: null };
  this.cache.set(key, node);
  this._attach(node);
  
  // Evict if over capacity
  if (this.cache.size > this.capacity) {
    const lruNode = this.tail.prev;
    this._detach(lruNode);
    this.cache.delete(lruNode.key);
  }
}
}

_detach(node) {
node.prev.next = node.next;
node.next.prev = node.prev;
}

_attach(node) {
node.prev = this.head;
node.next = this.head.next;
this.head.next.prev = node;
this.head.next = node;
}
}

module.exports = LRUCache;

text

## Test (Golden Assertions)
const lru = new LRUCache(2);
lru.put(1, 1); // capacity full
lru.put(2, 2);
expect(lru.get(1)).toBe(-1); // 1 evicted
expect(lru.get(2)).toBe(2); // 2 moved to MRU

text

## Key Techniques
- **Doubly Linked List**: O(1) detach/attach for eviction/promotion
- **HashMap**: O(1) key lookup
- **Tail as Sentinel**: Simplifies eviction logic

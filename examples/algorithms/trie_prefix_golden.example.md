---
id: "trie_prefix_golden"
source_story: "stories/algorithms/trie_implementation.story.md"
tags: ["algorithm", "trie", "prefix-tree", "string-matching"]
---

## Problem

Implement Trie for prefix matching.
- insert("apple")
- search("apple") → true
- search("app") → true
- startsWith("app") → true

## Solution

// path: src/algorithms/Trie.js
class TrieNode {
constructor() {
this.children = {};
this.isEnd = false;
}
}

class Trie {
constructor() {
this.root = new TrieNode();
}

insert(word) {
let node = this.root;
for (const char of word) {
if (!node.children[char]) {
node.children[char] = new TrieNode();
}
node = node.children[char];
}
node.isEnd = true;
}

search(word) {
const node = this._findNode(word);
return node && node.isEnd;
}

startsWith(prefix) {
return this._findNode(prefix) !== null;
}

_findNode(word) {
let node = this.root;
for (const char of word) {
if (!node.children[char]) return null;
node = node.children[char];
}
return node;
}
}

module.exports = Trie;

text

## Test (Golden Assertions)
const trie = new Trie();
trie.insert("apple");
expect(trie.search("apple")).toBe(true);
expect(trie.search("app")).toBe(false);
expect(trie.startsWith("app")).toBe(true);

text

## Key Techniques
- **HashMap Children**: O(1) character transitions
- **Terminal Flag**: `isEnd` distinguishes words from prefixes
- **Single Pass**: `_findNode()` handles both search/startsWith

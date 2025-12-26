---
id: "sliding_window_max_golden"
source_story: "stories/algorithms/sliding_window_max.story.md"
tags: ["algorithm", "deque", "sliding-window", "monotonic-queue"]
---

## Problem

Find maximum in sliding window of size k.
- nums = [1,3,-1,-3,5,3,6,7], k = 3
- Output: [3,3,5,5,6,7]

## Solution

// path: src/algorithms/slidingWindowMaximum.js
function maxSlidingWindow(nums, k) {
const result = [];
const deque = []; // stores indices, front = largest

for (let i = 0; i < nums.length; i++) {
// Remove indices out of current window
while (deque.length && deque <= i - k) {
deque.shift();
}

text
// Remove indices with smaller values (monotonic queue)
while (deque.length && nums[deque[deque.length - 1]] < nums[i]) {
  deque.pop();
}

// Add current index
deque.push(i);

// First valid window
if (i >= k - 1) {
  result.push(nums[deque]);
}
}

return result;
}

module.exports = maxSlidingWindow;

text

## Test (Golden Assertions)
expect(maxSlidingWindow([1,3,-1,-3,5,3,6,7], 3)).toEqual();
​
expect(maxSlidingWindow(, 1)).toEqual();
​

text

## Key Techniques
- **Monotonic Deque**: Decreasing order, front always largest
- **Window Cleanup**: Remove indices outside current window
- **O(N) Time**: Each element enqueued/dequeued at most once

---
id: "queue_jobs_golden"
source_story: "stories/backend/email_queue.story.md"
tags: ["background-jobs", "queue", "bull", "redis", "retries"]
---

## Problem

Process email notifications asynchronously:
- POST /users - Trigger welcome email on creation
- Failed emails retry 3x with exponential backoff
- Queue monitoring + dead letter queue
- Idempotent processing

## Solution

// path: src/queues/emailQueue.js
const Queue = require('bull');
const nodemailer = require('nodemailer');

const emailQueue = new Queue('email processing', process.env.REDIS_URL, {
defaultJobOptions: {
removeOnComplete: 100,
removeOnFail: 50,
attempts: 3,
backoff: { type: 'exponential', delay: 2000 }
}
});

// Email processor
emailQueue.process(async (job) => {
const { userId, template, idempotencyKey } = job.data;

// Idempotency check
const processed = await redis.get(email:${idempotencyKey});
if (processed) {
return { status: 'already_processed' };
}

const user = await User.findByPk(userId);
await sendEmail(user.email, template);

// Mark as processed
await redis.setex(email:${idempotencyKey}, 86400, 'sent');

return { status: 'sent', userId };
});

// Trigger welcome email
const queueWelcomeEmail = async (userId) => {
const idempotencyKey = welcome:${userId}:${Date.now()};

return emailQueue.add('welcome', {
userId,
template: 'welcome',
idempotencyKey
});
};

// Graceful shutdown
process.on('SIGTERM', async () => {
await emailQueue.close();
process.exit(0);
});

module.exports = { emailQueue, queueWelcomeEmail };

text

## Key Techniques
- **Bull Queue**: Redis-backed job processing with retries
- **Idempotency**: `idempotencyKey` prevents duplicate processing
- **Exponential Backoff**: Automatic retry strategy
- **Graceful Shutdown**: Drain queue before exit

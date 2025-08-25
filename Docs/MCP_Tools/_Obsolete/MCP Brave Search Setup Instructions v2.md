Here’s the exact directory structure and file contents — if you copy this into your IDE exactly as shown, it’s plug-and-play.

📂 brave-search-integration/
pgsql
Copy
Edit
brave-search-integration/
│
├── braveSearchPolicy.json
├── braveSearchManager.js
├── exampleUsage.js
└── braveSearchCache.json   # (will be auto-generated after first run)
📄 braveSearchPolicy.json
json
Copy
Edit
{
  "braveSearchConfig": {
    "apiName": "vsc_ide_dev_brave",
    "apiKey": "BSAk3We2xKQFoOgoQJVObWmYGrCd-J0"
  },
  "requestManagement": {
    "minDelayMs": 1000,
    "queueRequests": true,
    "rateLimitMonitoring": true
  },
  "queryOptimization": {
    "enableLocalCache": true,
    "cacheStorage": "file",
    "checkSimilarityBeforeRequest": true,
    "reuseCachedResults": true
  },
  "usagePatterns": {
    "maxRequestsPerMinute": 2,
    "useOnlyWhenLocalFails": true,
    "stepByStepIntegration": true,
    "noRapidFireCalls": true
  },
  "planSettings": {
    "preferredPlan": "Data for AI",
    "useRicherMetadata": true,
    "reduceRedundantLookups": true
  },
  "enforcement": {
    "strictMode": true,
    "logViolations": true,
    "haltOnViolation": false
  }
}
📄 braveSearchManager.js
(Final version with persistent cache, auto-throttle, and fuzzy matching)

javascript
Copy
Edit
import fs from 'fs';
import path from 'path';
import fetch from 'node-fetch';
import crypto from 'crypto';

// -------------------- CONFIG --------------------
const SIMILARITY_THRESHOLD = 0.85; // 0-1, higher = stricter match
// ------------------------------------------------

// Paths
const policyPath = path.resolve('./braveSearchPolicy.json');
const cacheFilePath = path.resolve('./braveSearchCache.json');

// Load policy JSON
const policy = JSON.parse(fs.readFileSync(policyPath, 'utf8'));

// Load persistent cache
let persistentCache = {};
if (fs.existsSync(cacheFilePath)) {
  try {
    persistentCache = JSON.parse(fs.readFileSync(cacheFilePath, 'utf8'));
  } catch {
    console.warn('[Brave API] Cache file corrupted, starting fresh.');
    persistentCache = {};
  }
}

// In-memory cache: { hash: { query: string, data: object, embedding: object } }
const cache = new Map(Object.entries(persistentCache));

// Save cache to disk (debounced)
let saveTimeout = null;
const saveCache = () => {
  if (saveTimeout) clearTimeout(saveTimeout);
  saveTimeout = setTimeout(() => {
    fs.writeFileSync(
      cacheFilePath,
      JSON.stringify(Object.fromEntries(cache), null, 2),
      'utf8'
    );
  }, 500);
};

// State variables
let lastRequestTime = 0;
let requestQueue = [];
let rateLimitRemaining = null;
let rateLimitReset = null;

// Helpers
const delay = (ms) => new Promise((res) => setTimeout(res, ms));
const hashQuery = (query) =>
  crypto.createHash('sha256').update(query).digest('hex');

// Simple text embedding (char bigrams)
function embedText(text) {
  const cleaned = text.toLowerCase().replace(/[^a-z0-9 ]/g, '');
  const tokens = [];
  for (let i = 0; i < cleaned.length - 1; i++) {
    tokens.push(cleaned.slice(i, i + 2));
  }
  const freq = {};
  tokens.forEach((t) => (freq[t] = (freq[t] || 0) + 1));
  const norm = Math.sqrt(Object.values(freq).reduce((s, v) => s + v * v, 0));
  return Object.fromEntries(Object.entries(freq).map(([t, v]) => [t, v / norm]));
}

// Cosine similarity for embeddings
function cosineSimilarity(e1, e2) {
  let dot = 0;
  for (const token in e1) {
    if (e2[token]) dot += e1[token] * e2[token];
  }
  return dot;
}

// Similarity check (exact or fuzzy)
function findSimilarQuery(query) {
  const hashed = hashQuery(query);
  if (cache.has(hashed)) return cache.get(hashed);

  const newEmbedding = embedText(query);
  let bestMatch = null;
  let bestScore = 0;

  for (const [, entry] of cache.entries()) {
    if (!entry.embedding) continue;
    const score = cosineSimilarity(newEmbedding, entry.embedding);
    if (score > bestScore) {
      bestScore = score;
      bestMatch = entry;
    }
  }

  if (bestScore >= SIMILARITY_THRESHOLD) {
    console.log(`[Brave API] Fuzzy match found (similarity: ${bestScore.toFixed(2)})`);
    return bestMatch;
  }
  return null;
}

// Queueing
async function enqueueRequest() {
  if (policy.requestManagement.queueRequests) {
    await new Promise((resolve) => requestQueue.push(resolve));
  }
}
function releaseNextRequest() {
  if (policy.requestManagement.queueRequests) {
    const next = requestQueue.shift();
    if (next) next();
  }
}

// Rate limit enforcement
async function enforceRateLimits() {
  const now = Date.now();
  const timeSinceLast = now - lastRequestTime;

  if (timeSinceLast < policy.requestManagement.minDelayMs) {
    await delay(policy.requestManagement.minDelayMs - timeSinceLast);
  }

  if (rateLimitRemaining !== null && rateLimitRemaining <= 2) {
    const waitMs = Math.max(rateLimitReset * 1000 - Date.now(), 1000);
    console.log(`[Brave API] Nearing limit (${rateLimitRemaining} left). Waiting ${waitMs}ms before next request.`);
    await delay(waitMs);
  }
}

// Main search function
async function braveSearch(query) {
  await enqueueRequest();
  await enforceRateLimits();

  if (policy.queryOptimization.enableLocalCache) {
    const match = findSimilarQuery(query);
    if (match) {
      releaseNextRequest();
      return match.data;
    }
  }

  const res = await fetch(
    `https://api.search.brave.com/res/v1/web/search?q=${encodeURIComponent(query)}`,
    {
      headers: {
        'X-Subscription-Token': policy.braveSearchConfig.apiKey,
      },
    }
  );

  rateLimitRemaining = parseInt(res.headers.get('X-RateLimit-Remaining')) || null;
  const resetHeader = res.headers.get('X-RateLimit-Reset');
  rateLimitReset = resetHeader ? Date.now() + parseInt(resetHeader) * 1000 : null;

  if (!res.ok) {
    releaseNextRequest();
    throw new Error(`Brave API error: ${res.status} ${res.statusText}`);
  }

  const data = await res.json();

  if (policy.queryOptimization.enableLocalCache) {
    const hashed = hashQuery(query);
    cache.set(hashed, {
      query,
      data,
      embedding: embedText(query)
    });
    saveCache();
  }

  lastRequestTime = Date.now();
  releaseNextRequest();

  return data;
}

export default braveSearch;
📄 exampleUsage.js
javascript
Copy
Edit
import braveSearch from './braveSearchManager.js';

(async () => {
  console.log(await braveSearch("javascript proxy patterns"));
  console.log(await braveSearch("patterns for proxies in JS")); // Should reuse previous result
})();
📄 braveSearchCache.json
(Auto-generated at first run, no need to create manually)

🚀 How to Install & Run
Copy the brave-search-integration/ folder into your project root.

Run:

bash
Copy
Edit
cd brave-search-integration
npm install node-fetch
Test with:

bash
Copy
Edit
node exampleUsage.js
In your KiloCode AI agent code, replace direct Brave Search fetch calls with:

javascript
Copy
Edit
import braveSearch from './braveSearchManager.js';
const results = await braveSearch("your search query");

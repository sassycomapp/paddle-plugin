import braveSearch from './braveSearchManager.js';

(async () => {
  console.log("Testing Brave Search with a new query...");
  try {
    const results1 = await braveSearch("javascript proxy patterns");
    console.log("Results for 'javascript proxy patterns':", JSON.stringify(results1, null, 2));
  } catch (error) {
    console.error("Error during first search:", error.message);
  }

  console.log("\nTesting Brave Search with a similar query (should use cache)...");
  try {
    const results2 = await braveSearch("patterns for proxies in JS");
    console.log("Results for 'patterns for proxies in JS':", JSON.stringify(results2, null, 2));
  } catch (error) {
    console.error("Error during second search:", error.message);
  }
})();

[X] Recursive summarization if the text is beyond 16k tokens, since model recall is usually best around 8-16k
[X] For large articles beyond 32k characters (not tokens), store the article in blob storage and not table storage.
[ ] Reddit r/news top 10
[ ] Hackernews front page
[ ] Straitstimes / mothership live stream
[ ] Improve access to medical articles
[X] Download already completed summaries and analyze them
[ ] Write a good README
[ ] Write a good blobg post
[ ] Make reporting posts actually do something
[ ] Cache user's last message in memory (for retrying)
[ ] /retry summaries if it's bad
[ ] Check blob storage for articles before doing a fetch (for retrying)

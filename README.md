# menplus Customer Insights

A small, **read-only** internal script used by menplus, a US big & tall menswear brand, to understand the fit and sizing problems big and tall men talk about on Reddit.

## What it does
- Once or twice a day, reads the newest public posts and their public comments from:
  r/malefashionadvice, r/bigmenfashion, r/tall, r/BigAndTall, r/frugalmalefashion
- Uses only the OAuth `read` scope and standard read endpoints (`/r/{sub}/new`, `/comments/{id}`).
- Saves post titles, post text and comment text to a private local file. **No usernames, private messages or voting data are stored.**
- Our team reads and summarizes the text manually to improve product fit and size charts.

## What it never does
- Never posts, comments, votes or sends messages.
- Never resells or shares Reddit data, and never uses it to train AI models.

## Rate limits
About 100–300 requests per day, with a 2-second delay between requests and a descriptive User-Agent.

## Data deletion
Saved data is deleted within 48 hours when Reddit or a user requests it (`delete_ids()` in `reddit_reader.py`).

## Privacy policy
https://ducbeo93.github.io/menplus-reddit-insights/

Source: https://github.com/ducbeo93/menplus-reddit-insights

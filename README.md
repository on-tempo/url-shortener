# URL Shortener

A URL shortener built with FastAPI, SQLite, and Redis.

This is my second backend project. I built it to understand caching and how a read-heavy service works, not just to make it run. Most of the design choices below came from asking "why" for each part, so I tried to write down the reasoning instead of only the steps.

## What it does

- Shorten a long URL into a 7-character code
- Redirect from the short code to the original URL
- Count how many times a short link was clicked
- Optional expiration date for a link
- Delete a short link

## Tech stack

| Part | Choice |
|------|--------|
| Backend | FastAPI (Python) |
| Database | SQLite (will move to PostgreSQL later) |
| Cache | Redis |
| Validation | Pydantic |

## How the short code works

The short code is 7 characters from `a-z`, `A-Z`, `0-9` (62 characters total).
That gives 62^7, which is about 3.5 trillion combinations, so collisions are
extremely rare at this scale.

I do not compare a new code against every existing one in the app. Instead the
`short_code` column has a `unique` constraint in the database, so the database
itself rejects duplicates. This also means an old code is never reused, even
after a link is deleted, which avoids sending an old saved link to a new wrong
destination.

## Caching (the main thing I wanted to learn)

Redirects happen far more often than creating links, so I cache the
`code -> URL` mapping in Redis (cache-aside):

1. On redirect, check Redis first.
2. If it is there (cache hit), redirect right away.
3. If not (cache miss), read from the DB, store it in Redis, then redirect.

Cached entries get a 1 hour TTL so the cache does not hold stale data forever.

When a link is updated or deleted, I **delete** the Redis copy instead of
overwriting it. A wrong value left in the cache is worse than a slightly slower
DB read, so deleting and letting the next request reload from the DB is the
safer choice.

## Redis is treated as optional

Redis is only a speed-up, not the source of truth. So every Redis call is
wrapped so that if Redis is down, the request still works using the database
(just slower). For example, a redirect still works without Redis; it just skips
the cache and click counting. The DB is the part that must not fail.

## Expiration

`expires_at` is checked against the database, which is the source of truth, not
against the Redis TTL. The Redis TTL is only for cache freshness. A link with no
expiration date is allowed (the column is nullable).

## Click counting

Each redirect increments a counter in Redis (`clicks:<code>`). Reading from
Redis on every click is cheap, so this avoids writing to the DB on every single
click. (Periodically flushing these counts back into the DB is something I plan
to add later.)

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/shorten` | Create a short code for a URL (optional `expires_in_days`) |
| GET | `/{short_code}` | Redirect to the original URL |
| DELETE | `/{short_code}` | Delete a short code (also clears its cache) |
| GET | `/{short_code}/clicks` | Get the click count for a code |

Interactive docs are at `/docs` when the server is running.

## Running locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Start Redis with Docker:

```bash
docker run -d --name redis-url -p 6379:6379 redis
```

Run the server:

```bash
uvicorn main:app --reload
```

Then open `http://localhost:8000/docs`.

## Notes / things to improve

- Move from SQLite to PostgreSQL and run everything with docker-compose
- Flush Redis click counts into the DB periodically
- The expiration check currently runs on the DB path; the cache-hit path skips
  it, which I left as a known trade-off for now

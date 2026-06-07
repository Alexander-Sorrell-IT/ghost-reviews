"""Offline sample reviews — Amazon-style, so the app runs + demos before Nimble.

Mix of real human reviews (specific, balanced, varied ratings) and AI-written
ones (generic, hyped, steering the rating). Each has a star rating so we can
show the 'humans say X, AI is faking Y' gap. Swapped for live Nimble data once
NIMBLE_API_KEY is set.
"""

SAMPLE_REVIEWS = [
    {
        "title": "BEST EARBUDS EVER!!!",
        "text": "These are absolutely the best earbuds on the market! Amazing "
        "sound, amazing battery, amazing everything. The Acme Wireless Earbuds "
        "are a must buy. Five stars, highly recommend to everyone!!!",
        "rating": 5,
        "url": "https://www.amazon.com/gp/customer-reviews/R1",
        "source": {"reviewer": "user_8842"},
    },
    {
        "title": "Decent but the case creaks",
        "text": "Had these about three weeks. Sound is solid for the price, bass "
        "is weak on noisy bus rides. The charging case lid creaks and the left "
        "bud disconnects if my phone's in my back pocket. Still using them daily.",
        "rating": 3,
        "url": "https://www.amazon.com/gp/customer-reviews/R2",
        "source": {"reviewer": "marcus_t"},
    },
    {
        "title": "Incredible! A must buy!",
        "text": "I am so happy with this purchase! Best earbuds on the market. "
        "The Acme Wireless Earbuds are simply the best in every way. Buy them now, "
        "you will not regret it. Perfect product, perfect price!",
        "rating": 5,
        "url": "https://www.amazon.com/gp/customer-reviews/R3",
        "source": {"reviewer": "user_9911"},
    },
    {
        "title": "Good for the gym, bad for calls",
        "text": "Bought these for running. They stay in fine and the sweat "
        "resistance held up over two months. Call quality is the weak point — "
        "coworkers say I sound far away and robotic. For music and workouts, no "
        "complaints though.",
        "rating": 4,
        "url": "https://www.amazon.com/gp/customer-reviews/R4",
        "source": {"reviewer": "dana_runs"},
    },
    {
        "title": "Amazing quality must buy 5 stars",
        "text": "Great product great seller fast shipping amazing quality five "
        "stars highly recommended best purchase will buy again amazing amazing "
        "amazing.",
        "rating": 5,
        "url": "https://www.amazon.com/gp/customer-reviews/R5",
        "source": {"reviewer": "user_1003"},
    },
    {
        "title": "Returned after a week",
        "text": "Wanted to like these. The right earbud stopped charging after "
        "five days no matter which case slot I used. Support was slow but did "
        "approve the return. Build quality felt cheap vs my old pair. Two stars "
        "for the easy refund.",
        "rating": 2,
        "url": "https://www.amazon.com/gp/customer-reviews/R6",
        "source": {"reviewer": "priya_k"},
    },
    {
        "title": "Flawless, you will love it",
        "text": "Received the Acme Wireless Earbuds and they are fantastic! "
        "Absolutely flawless performance. Everyone should buy these incredible "
        "earbuds, they are the best, a perfect 5 star product!",
        "rating": 5,
        "url": "https://www.amazon.com/gp/customer-reviews/R7",
        "source": {"reviewer": "review_club_22"},
    },
    {
        "title": "Battery is the real story",
        "text": "Three months in. Spec says 8 hours, I get about 5.5 at 60% "
        "volume, fine for my commute. Pairing is instant on Android, flaky on my "
        "work laptop. Touch controls too sensitive — I pause songs by accident.",
        "rating": 4,
        "url": "https://www.amazon.com/gp/customer-reviews/R8",
        "source": {"reviewer": "kenji_o"},
    },
]


def sample_reviews(max_results: int = 10):
    return SAMPLE_REVIEWS[:max_results]

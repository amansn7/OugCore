"""
Google Trends integration via pytrends (no API key required).
Industry secret: target 'rising' queries, not 'top' — find products
before they peak for early-mover advantage.
"""
import logging
import time

logger = logging.getLogger(__name__)

# Niche keyword seeds to research
DEFAULT_NICHES = [
    "home gadgets",
    "pet accessories",
    "fitness equipment",
    "kitchen tools",
    "phone accessories",
]


def get_rising_trends(niches=None, timeframe="today 3-m", geo="US"):
    """
    Return a dict mapping niche → list of rising related queries.
    Falls back to empty dict if pytrends is unavailable or rate-limited.
    """
    if niches is None:
        niches = DEFAULT_NICHES

    results = {}
    try:
        from pytrends.request import TrendReq

        try:
            pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        except Exception as exc:
            logger.warning("pytrends init failed (network unavailable): %s", exc)
            return results

        for niche in niches:
            try:
                pytrends.build_payload([niche], timeframe=timeframe, geo=geo)
                related = pytrends.related_queries()
                rising_df = related.get(niche, {}).get("rising")
                if rising_df is not None and not rising_df.empty:
                    results[niche] = rising_df["query"].tolist()[:10]
                else:
                    results[niche] = []
                time.sleep(1.5)  # respect rate limit
            except Exception as exc:
                logger.warning("pytrends query failed for '%s': %s", niche, exc)
                results[niche] = []

    except ImportError:
        logger.warning("pytrends not installed — returning empty trends")

    return results


def score_trend(keyword, timeframe="today 3-m", geo="US"):
    """
    Return a 0-100 trend score for a single keyword.
    Uses the average interest over time from Google Trends.
    """
    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        pytrends.build_payload([keyword], timeframe=timeframe, geo=geo)
        df = pytrends.interest_over_time()
        if df.empty:
            return 0
        return round(float(df[keyword].mean()), 1)
    except Exception as exc:
        logger.warning("Trend score failed for '%s': %s", keyword, exc)
        return 0

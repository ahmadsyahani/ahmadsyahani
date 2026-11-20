import datetime as dt


def summarize_activity(days, as_of):
    observed = sorted((dt.date.fromisoformat(date), count) for date, count, _ in days if date <= as_of.isoformat())
    if not observed:
        raise ValueError('No contribution data on or before the reporting date')
    end = min(as_of, observed[-1][0])
    year, month = divmod(end.year * 12 + end.month - 1 - 11, 12)
    start = dt.date(year, month + 1, 1)
    period = [(date, count) for date, count in observed if date >= start]
    months = {}
    for offset in range(12):
        year, month = divmod(start.year * 12 + start.month - 1 + offset, 12)
        months[f'{year:04d}-{month+1:02d}'] = 0
    longest = run = 0
    previous = None
    for date, count in period:
        run = run + 1 if count > 0 and previous == date - dt.timedelta(days=1) else int(count > 0)
        longest = max(longest, run)
        previous = date
        months[date.strftime('%Y-%m')] += count
    counts = dict(period)
    cursor = end if counts.get(end, 0) else end - dt.timedelta(days=1)
    current = 0
    while counts.get(cursor, 0) > 0:
        current += 1
        cursor -= dt.timedelta(days=1)
    return {
        'start': start.isoformat(), 'end': end.isoformat(),
        'total': sum(counts.values()), 'active': sum(count > 0 for count in counts.values()),
        'days': len(period), 'current_streak': current, 'longest_streak': longest,
        'best_day': max(counts.values()), 'months': list(months.items()),
        'peak_month': max(months.values()),
    }

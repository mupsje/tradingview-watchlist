"""Shared constants for volume buckets and thresholds."""

# Minimum 24h volume thresholds (in USD)
VOLUME_THRESHOLDS: list[int] = [500_000, 1_000_000, 5_000_000]

# Human-readable bucket labels keyed by min_volume
VOLUME_BUCKET_LABELS: dict[int, str] = {
    500_000: '500K-1000K',
    1_000_000: '1M-5M',
    5_000_000: '5M+',
}

# Reverse map: label → threshold (used by analysis scripts)
LABEL_TO_VOLUME: dict[str, int] = {v: k for k, v in VOLUME_BUCKET_LABELS.items()}

# Volume bucket label list (used by marketcap_bucket.py iteration)
VOLUME_BUCKETS: list[str] = list(VOLUME_BUCKET_LABELS.values())


def get_volume_bucket_label(min_volume: float) -> str:
    """Return the human-readable bucket label for a given volume threshold."""
    try:
        return VOLUME_BUCKET_LABELS[int(min_volume)]
    except (KeyError, ValueError, TypeError):
        return f"{int(min_volume / 1000)}K"


def parse_volume_bucket(bucket_label: str) -> int:
    """Parse a directory label like '500K-1000K' or '5M+' back to the min threshold."""
    if bucket_label in LABEL_TO_VOLUME:
        return LABEL_TO_VOLUME[bucket_label]
    if bucket_label.endswith('+'):
        return int(bucket_label[:-1].replace('M', '000000').replace('K', '000'))
    if '-' in bucket_label:
        return int(bucket_label.split('-')[0].replace('M', '000000').replace('K', '000'))
    return int(bucket_label.replace('M', '000000').replace('K', '000'))

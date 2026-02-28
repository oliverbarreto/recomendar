"""
Audio quality value object for YouTube download preferences
"""
from enum import Enum
from typing import Tuple, Optional


class AudioQualityTier(Enum):
    """Audio quality tiers for download preferences"""
    LOW = "low"        # 0-70 kbps
    MEDIUM = "medium"  # 70-150 kbps
    HIGH = "high"      # 150+ kbps

    @classmethod
    def from_bitrate(cls, abr: float) -> 'AudioQualityTier':
        """Determine quality tier from a bitrate value (kbps)"""
        if abr <= 70:
            return cls.LOW
        elif abr <= 150:
            return cls.MEDIUM
        else:
            return cls.HIGH

    @classmethod
    def from_string(cls, value: Optional[str]) -> Optional['AudioQualityTier']:
        """Parse a string value into a quality tier, or None"""
        if not value:
            return None
        try:
            return cls(value.lower())
        except ValueError:
            return None

    @property
    def bitrate_range(self) -> Tuple[float, float]:
        """Return (min_kbps, max_kbps) for this tier"""
        ranges = {
            AudioQualityTier.LOW: (0, 70),
            AudioQualityTier.MEDIUM: (70, 150),
            AudioQualityTier.HIGH: (150, float('inf')),
        }
        return ranges[self]

    @property
    def preferred_yt_dlp_quality(self) -> str:
        """Return the preferred FFmpeg post-processor quality for this tier"""
        qualities = {
            AudioQualityTier.LOW: '64',
            AudioQualityTier.MEDIUM: '128',
            AudioQualityTier.HIGH: '192',
        }
        return qualities[self]

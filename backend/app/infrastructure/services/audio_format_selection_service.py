"""
Audio Format Selection Service

Analyzes yt-dlp format lists and builds optimal format selector strings
based on user-requested language and quality preferences.
"""
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from app.domain.value_objects.audio_quality import AudioQualityTier

logger = logging.getLogger(__name__)


@dataclass
class AudioFormatSelectionResult:
    """Result of format selection analysis"""
    format_selector: str
    preferred_quality_kbps: str
    actual_language: Optional[str] = None
    actual_quality: Optional[str] = None
    fallback_occurred: bool = False
    fallback_reason: Optional[str] = None


class AudioFormatSelectionService:
    """
    Analyzes available audio formats from yt-dlp and selects the best match
    for the user's language and quality preferences.
    """

    # Default format selector (current behavior)
    DEFAULT_FORMAT = 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best[height<=480]'
    DEFAULT_QUALITY = '192'

    @staticmethod
    def build_format_selector(
        requested_language: Optional[str],
        requested_quality: Optional[str]
    ) -> tuple:
        """
        Build a yt-dlp format selector string using native language filtering.

        Instead of manually parsing format lists and picking format IDs,
        this builds a selector string that lets yt-dlp handle format resolution
        natively during download. This avoids mismatch bugs between format
        analysis and download phases.

        Uses ^= (starts-with) for language matching to handle regional
        variants like es-419, es-ES, etc.

        Args:
            requested_language: ISO 639-1 language code (e.g., "es") or None
            requested_quality: Quality tier ("low"/"medium"/"high") or None

        Returns:
            Tuple of (format_selector_string, preferred_quality_kbps)
        """
        DEFAULT_FORMAT = 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best[height<=480]'

        quality_tier = AudioQualityTier.from_string(requested_quality)
        preferred_kbps = quality_tier.preferred_yt_dlp_quality if quality_tier else '192'

        if not requested_language:
            return (DEFAULT_FORMAT, preferred_kbps)

        # Language-aware selector with fallback chain:
        # 1. bestaudio[language^=XX] — DASH audio-only in requested language
        # 2. best[language^=XX][height<=480] — HLS combined (low res) in requested language
        # 3. best[language^=XX] — HLS combined (any res) in requested language
        # 4-7. DEFAULT_FORMAT — fallback to best available (any language)
        lang = requested_language
        format_selector = (
            f'bestaudio[language^={lang}]/'
            f'best[language^={lang}][height<=480]/'
            f'best[language^={lang}]/'
            + DEFAULT_FORMAT
        )

        logger.info(
            f"[FORMAT_SELECTOR] Built selector for language='{lang}', "
            f"quality='{requested_quality}': {format_selector} "
            f"(ffmpeg quality={preferred_kbps}kbps)"
        )

        return (format_selector, preferred_kbps)

    def select_format(
        self,
        formats: Optional[List[Dict[str, Any]]],
        requested_language: Optional[str],
        requested_quality: Optional[str]
    ) -> AudioFormatSelectionResult:
        """
        Select the best audio format based on user preferences.

        Args:
            formats: List of format dicts from yt-dlp's extract_info()
            requested_language: ISO 639-1 language code or None
            requested_quality: Quality tier string ("low"/"medium"/"high") or None

        Returns:
            AudioFormatSelectionResult with format selector and metadata
        """
        # If no preferences specified, use default behavior
        if not requested_language and not requested_quality:
            return AudioFormatSelectionResult(
                format_selector=self.DEFAULT_FORMAT,
                preferred_quality_kbps=self.DEFAULT_QUALITY
            )

        quality_tier = AudioQualityTier.from_string(requested_quality)

        # If no formats available (e.g., extract_info failed), use defaults with requested quality
        if not formats:
            logger.warning("No formats list available, using default format with requested quality")
            preferred_kbps = quality_tier.preferred_yt_dlp_quality if quality_tier else self.DEFAULT_QUALITY
            return AudioFormatSelectionResult(
                format_selector=self.DEFAULT_FORMAT,
                preferred_quality_kbps=preferred_kbps,
                actual_quality=requested_quality,
                fallback_occurred=True,
                fallback_reason="No format list available from yt-dlp"
            )

        # Filter to audio-only formats
        audio_formats = self._get_audio_formats(formats)
        if not audio_formats:
            logger.warning("No audio-only formats found, using default format")
            preferred_kbps = quality_tier.preferred_yt_dlp_quality if quality_tier else self.DEFAULT_QUALITY
            return AudioFormatSelectionResult(
                format_selector=self.DEFAULT_FORMAT,
                preferred_quality_kbps=preferred_kbps,
                fallback_occurred=True,
                fallback_reason="No audio-only formats found"
            )

        return self._select_with_fallback(
            audio_formats, requested_language, quality_tier
        )

    def _get_audio_formats(self, formats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter to audio-only formats OR formats with language metadata.

        Supports both DASH audio-only streams and HLS multi-language streams.
        """
        audio_formats = []
        dash_audio_count = 0
        hls_multilang_count = 0
        available_languages: set = set()

        for fmt in formats:
            vcodec = fmt.get('vcodec', '')
            acodec = fmt.get('acodec', '')
            format_note = fmt.get('format_note', '').lower()
            format_id = fmt.get('format_id', '')
            resolution = fmt.get('resolution', '')
            language = fmt.get('language')
            protocol = fmt.get('protocol', '')

            # Skip storyboard formats (thumbnail images)
            if 'storyboard' in format_note or format_id.startswith('sb'):
                continue

            # Skip image formats
            if vcodec == 'none' and acodec == 'none':
                continue

            # Track all languages seen across all formats
            if language:
                available_languages.add(language)

            # Three categories of formats we want:
            # 1. DASH audio-only (vcodec=none, has acodec)
            # 2. Formats explicitly marked as "audio only"
            # 3. HLS multi-language formats (have language metadata, even if combined video+audio)

            is_audio_format = False

            # DASH audio-only streams
            if vcodec == 'none' and acodec and acodec != 'none':
                is_audio_format = True
                dash_audio_count += 1
            # Explicitly marked audio-only
            elif 'audio only' in format_note or 'audio only' in resolution:
                is_audio_format = True
                dash_audio_count += 1
            # HLS multi-language streams (we can extract audio from these)
            elif language and protocol in ('m3u8', 'm3u8_native', 'https'):
                is_audio_format = True
                hls_multilang_count += 1
                # Add a marker to indicate this needs audio extraction
                fmt['_requires_audio_extraction'] = True

            if is_audio_format:
                audio_formats.append(fmt)

        # Structured summary log — replaces verbose per-format logging
        logger.info(
            f"[FORMATS] Total: {len(formats)}, "
            f"DASH audio: {dash_audio_count}, "
            f"HLS multi-lang: {hls_multilang_count}, "
            f"Selected: {len(audio_formats)}"
        )
        if available_languages:
            logger.info(f"[FORMATS] Available languages: {{{', '.join(sorted(available_languages))}}}")
        else:
            logger.info("[FORMATS] No language metadata found on any format")

        return audio_formats

    def _select_with_fallback(
        self,
        audio_formats: List[Dict[str, Any]],
        requested_language: Optional[str],
        quality_tier: Optional[AudioQualityTier]
    ) -> AudioFormatSelectionResult:
        """
        Try to find the best match with fallback chain:
        1. Exact language + quality match
        2. Same language, higher quality
        3. Same language, lower quality
        4. Any language with requested quality (fallback to original)
        """
        # Determine available languages
        available_languages = set()
        for fmt in audio_formats:
            lang = fmt.get('language')
            if lang:
                available_languages.add(lang)

        has_language_data = len(available_languages) > 0

        # If language requested but no language metadata available, skip language filtering
        if requested_language and not has_language_data:
            logger.info(f"Requested language '{requested_language}' but no language metadata on formats")
            return self._select_by_quality_only(
                audio_formats, quality_tier,
                fallback_reason=f"No language metadata available; requested '{requested_language}'"
            )

        # If language requested, try language-filtered formats
        if requested_language and has_language_data:
            lang_formats = [
                f for f in audio_formats
                if f.get('language', '').startswith(requested_language)
            ]

            if lang_formats:
                # Try exact quality match
                if quality_tier:
                    result = self._find_quality_match(lang_formats, quality_tier, requested_language)
                    if result:
                        return result

                # If no quality preference or no quality match, pick best in language
                best = self._pick_best_format(lang_formats)
                actual_quality = self._determine_quality_tier(best)
                fallback = quality_tier is not None
                return AudioFormatSelectionResult(
                    format_selector=best.get('format_id', self.DEFAULT_FORMAT),
                    preferred_quality_kbps=quality_tier.preferred_yt_dlp_quality if quality_tier else self.DEFAULT_QUALITY,
                    actual_language=requested_language,
                    actual_quality=actual_quality,
                    fallback_occurred=fallback,
                    fallback_reason=f"Quality '{quality_tier.value}' not available in '{requested_language}'; using best available" if fallback else None
                )
            else:
                # Language not available at all - fallback to default
                logger.info(f"Language '{requested_language}' not available, falling back to default")
                return self._select_by_quality_only(
                    audio_formats, quality_tier,
                    fallback_reason=f"Language '{requested_language}' not available; available: {', '.join(sorted(available_languages))}"
                )

        # No language preference, just quality
        return self._select_by_quality_only(audio_formats, quality_tier)

    def _select_by_quality_only(
        self,
        audio_formats: List[Dict[str, Any]],
        quality_tier: Optional[AudioQualityTier],
        fallback_reason: Optional[str] = None
    ) -> AudioFormatSelectionResult:
        """Select format based on quality preference only"""
        if quality_tier:
            result = self._find_quality_match(audio_formats, quality_tier)
            if result:
                if fallback_reason:
                    result.fallback_occurred = True
                    result.fallback_reason = fallback_reason
                return result

        # Pick best available
        best = self._pick_best_format(audio_formats)
        actual_quality = self._determine_quality_tier(best)
        preferred_kbps = quality_tier.preferred_yt_dlp_quality if quality_tier else self.DEFAULT_QUALITY

        return AudioFormatSelectionResult(
            format_selector=best.get('format_id', self.DEFAULT_FORMAT),
            preferred_quality_kbps=preferred_kbps,
            actual_quality=actual_quality,
            fallback_occurred=fallback_reason is not None or quality_tier is not None,
            fallback_reason=fallback_reason or (f"No formats matching quality '{quality_tier.value}'; using best available" if quality_tier else None)
        )

    def _find_quality_match(
        self,
        formats: List[Dict[str, Any]],
        quality_tier: AudioQualityTier,
        language: Optional[str] = None
    ) -> Optional[AudioFormatSelectionResult]:
        """
        Find formats matching the quality tier's bitrate range.

        Supports both DASH audio-only (with abr) and HLS combined video+audio (with tbr).
        For HLS formats, selects based on resolution as a proxy for audio quality.
        """
        min_br, max_br = quality_tier.bitrate_range

        # First try DASH audio-only formats (with abr)
        matching_audio_only = [
            f for f in formats
            if f.get('abr') and min_br <= f['abr'] <= max_br
        ]

        if matching_audio_only:
            # Pick the one closest to the tier's preferred bitrate
            target = int(quality_tier.preferred_yt_dlp_quality)
            best = min(matching_audio_only, key=lambda f: abs(f.get('abr', 0) - target))
            return AudioFormatSelectionResult(
                format_selector=best.get('format_id', self.DEFAULT_FORMAT),
                preferred_quality_kbps=quality_tier.preferred_yt_dlp_quality,
                actual_language=language,
                actual_quality=quality_tier.value,
                fallback_occurred=False,
                fallback_reason=None
            )

        # Fall back to HLS combined formats (select by resolution)
        # LOW: 144p or 240p, MEDIUM: 360p or 480p, HIGH: 720p or 1080p+
        hls_formats = [f for f in formats if f.get('protocol') in ('m3u8', 'm3u8_native')]
        if hls_formats:
            resolution_map = {
                'low': ['144', '240'],
                'medium': ['360', '480'],
                'high': ['720', '1080', '1440', '2160']
            }
            target_resolutions = resolution_map.get(quality_tier.value, ['360'])

            # Try to find format matching desired resolution
            for res in target_resolutions:
                matching_hls = [
                    f for f in hls_formats
                    if res in f.get('resolution', '') or res in f.get('format_note', '')
                ]
                if matching_hls:
                    # Pick the first match (they're similar quality)
                    best = matching_hls[0]
                    logger.info(
                        f"Selected HLS format {best.get('format_id')} "
                        f"({best.get('resolution')}) for {quality_tier.value} quality"
                    )
                    return AudioFormatSelectionResult(
                        format_selector=best.get('format_id', self.DEFAULT_FORMAT),
                        preferred_quality_kbps=quality_tier.preferred_yt_dlp_quality,
                        actual_language=language,
                        actual_quality=quality_tier.value,
                        fallback_occurred=False,
                        fallback_reason=None
                    )

        return None

    def _pick_best_format(self, formats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Pick the best format by bitrate.

        Prefers DASH audio-only (highest abr), then HLS combined (lowest resolution
        for efficiency since audio quality is similar across resolutions).
        """
        # First try DASH audio-only formats (highest abr = best quality)
        with_abr = [f for f in formats if f.get('abr')]
        if with_abr:
            return max(with_abr, key=lambda f: f['abr'])

        # For HLS combined formats, prefer lowest resolution (360p) for efficiency
        # Audio quality is similar across resolutions, so minimize bandwidth
        hls_formats = [f for f in formats if f.get('protocol') in ('m3u8', 'm3u8_native')]
        if hls_formats:
            # Prefer 360p or 480p (good balance of quality and size)
            for res in ['360', '480', '240', '720']:
                matching = [
                    f for f in hls_formats
                    if res in f.get('resolution', '') or res in f.get('format_note', '')
                ]
                if matching:
                    logger.info(
                        f"Selected HLS format {matching[0].get('format_id')} "
                        f"({matching[0].get('resolution')}) as best available"
                    )
                    return matching[0]
            # Fallback to first HLS format
            return hls_formats[0]

        # Last resort: prefer m4a > mp3 > anything
        for ext in ('m4a', 'mp3'):
            ext_formats = [f for f in formats if f.get('ext') == ext]
            if ext_formats:
                return ext_formats[0]

        return formats[0] if formats else {}

    def _determine_quality_tier(self, fmt: Dict[str, Any]) -> Optional[str]:
        """
        Determine which quality tier a format falls into.

        For DASH audio-only: uses abr (audio bitrate).
        For HLS combined: uses resolution as proxy for quality tier.
        """
        # DASH audio-only formats
        abr = fmt.get('abr')
        if abr:
            return AudioQualityTier.from_bitrate(abr).value

        # HLS combined formats - determine by resolution
        resolution = fmt.get('resolution', '')
        format_note = fmt.get('format_note', '')
        combined = f"{resolution} {format_note}".lower()

        if any(res in combined for res in ['144', '240']):
            return 'low'
        elif any(res in combined for res in ['360', '480']):
            return 'medium'
        elif any(res in combined for res in ['720', '1080', '1440', '2160']):
            return 'high'

        return None

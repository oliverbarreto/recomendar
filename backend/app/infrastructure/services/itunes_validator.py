"""
iTunes Podcast Specification Validator
"""
from typing import List, Dict, Any, Optional
from xml.etree import ElementTree as ET
import re
from datetime import datetime
import requests
from PIL import Image
import io


class iTunesValidator:
    """
    Validates RSS feeds against iTunes Podcast Specifications
    """
    
    def __init__(self):
        self.itunes_ns = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'}
        self.required_channel_elements = [
            'title', 'description', 'link', 'language', 'lastBuildDate'
        ]
        self.required_itunes_elements = [
            'itunes:author', 'itunes:category', 'itunes:image', 
            'itunes:explicit', 'itunes:owner'
        ]
        self.valid_languages = self._load_language_codes()
        self.valid_categories = self._load_itunes_categories()
    
    def validate_full_feed(self, feed_xml: str) -> Dict[str, Any]:
        """
        Comprehensive iTunes feed validation
        
        Returns:
            Dict with validation results including score, errors, warnings, and recommendations
        """
        result = {
            'is_valid': False,
            'score': 0.0,
            'errors': [],
            'warnings': [],
            'recommendations': [],
            'validation_details': {}
        }
        
        try:
            root = ET.fromstring(feed_xml)
            channel = root.find('.//channel')
            
            if channel is None:
                result['errors'].append('Missing required <channel> element')
                return result
            
            # Validate channel-level elements
            channel_validation = self._validate_channel(channel)
            result['errors'].extend(channel_validation['errors'])
            result['warnings'].extend(channel_validation['warnings'])
            result['recommendations'].extend(channel_validation['recommendations'])
            
            # Validate episodes
            episodes = root.findall('.//item')
            episode_validation = self._validate_episodes(episodes)
            result['errors'].extend(episode_validation['errors'])
            result['warnings'].extend(episode_validation['warnings'])
            result['recommendations'].extend(episode_validation['recommendations'])
            
            # Validate iTunes-specific elements
            itunes_validation = self._validate_itunes_elements(root)
            result['errors'].extend(itunes_validation['errors'])
            result['warnings'].extend(itunes_validation['warnings'])
            result['recommendations'].extend(itunes_validation['recommendations'])
            
            # Calculate compliance score
            result['score'] = self._calculate_compliance_score(
                root, len(result['errors']), len(result['warnings'])
            )
            
            result['is_valid'] = len(result['errors']) == 0
            result['validation_details'] = {
                'total_episodes': len(episodes),
                'channel_complete': len(channel_validation['errors']) == 0,
                'itunes_complete': len(itunes_validation['errors']) == 0,
                'episodes_valid': len(episode_validation['errors']) == 0
            }
            
        except ET.ParseError as e:
            result['errors'].append(f'XML parsing error: {str(e)}')
        
        return result
    
    def _validate_channel(self, channel: ET.Element) -> Dict[str, List[str]]:
        """Validate RSS channel elements"""
        errors, warnings, recommendations = [], [], []
        
        # Required RSS elements
        for element in self.required_channel_elements:
            elem = channel.find(element)
            if elem is None:
                errors.append(f'Missing required element: {element}')
            elif element == 'description' and elem.text and len(elem.text) < 50:
                warnings.append('Channel description should be at least 50 characters')
            elif element == 'title' and elem.text and len(elem.text) > 255:
                warnings.append('Channel title should be under 255 characters')
        
        # Language validation
        lang_elem = channel.find('language')
        if lang_elem is not None and lang_elem.text:
            if lang_elem.text not in self.valid_languages:
                warnings.append(f'Language code "{lang_elem.text}" may not be recognized by iTunes')
        
        return {'errors': errors, 'warnings': warnings, 'recommendations': recommendations}
    
    def _validate_itunes_elements(self, root: ET.Element) -> Dict[str, List[str]]:
        """Validate iTunes-specific elements"""
        errors, warnings, recommendations = [], [], []
        
        # Required iTunes elements
        for xpath in self.required_itunes_elements:
            elem = root.find(f'.//{xpath}', self.itunes_ns)
            if elem is None:
                errors.append(f'Missing required iTunes element: {xpath}')
        
        # iTunes image validation
        image_elem = root.find('.//itunes:image', self.itunes_ns)
        if image_elem is not None:
            href = image_elem.get('href')
            if href:
                image_validation = self._validate_itunes_image(href)
                errors.extend(image_validation['errors'])
                warnings.extend(image_validation['warnings'])
                recommendations.extend(image_validation['recommendations'])
        
        # iTunes category validation
        category_elem = root.find('.//itunes:category', self.itunes_ns)
        if category_elem is not None:
            text = category_elem.get('text', '')
            if text not in self.valid_categories:
                warnings.append(f'iTunes category "{text}" may not be recognized')
        
        # iTunes explicit validation
        explicit_elem = root.find('.//itunes:explicit', self.itunes_ns)
        if explicit_elem is not None:
            value = explicit_elem.text
            if value not in ['true', 'false', 'yes', 'no', 'clean']:
                warnings.append(f'iTunes explicit value "{value}" should be true/false/yes/no/clean')
        
        # iTunes owner validation
        owner_elem = root.find('.//itunes:owner', self.itunes_ns)
        if owner_elem is not None:
            name_elem = owner_elem.find('itunes:name', self.itunes_ns)
            email_elem = owner_elem.find('itunes:email', self.itunes_ns)
            
            if name_elem is None:
                errors.append('iTunes owner missing name element')
            if email_elem is None:
                errors.append('iTunes owner missing email element')
            elif email_elem.text and not self._is_valid_email(email_elem.text):
                errors.append('iTunes owner email is not valid')
        
        return {'errors': errors, 'warnings': warnings, 'recommendations': recommendations}
    
    def _validate_episodes(self, episodes: List[ET.Element]) -> Dict[str, List[str]]:
        """Validate episode elements"""
        errors, warnings, recommendations = [], [], []
        
        if not episodes:
            warnings.append('No episodes found in feed')
            return {'errors': errors, 'warnings': warnings, 'recommendations': recommendations}
        
        for i, episode in enumerate(episodes, 1):
            # Required episode elements
            title_elem = episode.find('title')
            if title_elem is None:
                errors.append(f'Episode {i}: Missing title')
            elif title_elem.text and len(title_elem.text) > 255:
                warnings.append(f'Episode {i}: Title should be under 255 characters')
            
            description_elem = episode.find('description')
            if description_elem is None:
                errors.append(f'Episode {i}: Missing description')
            elif description_elem.text and len(description_elem.text) < 100:
                recommendations.append(f'Episode {i}: Description should be at least 100 characters for better SEO')
            
            # Enclosure validation
            enclosure = episode.find('enclosure')
            if enclosure is None:
                errors.append(f'Episode {i}: Missing enclosure (media file)')
            else:
                url = enclosure.get('url')
                length = enclosure.get('length')
                media_type = enclosure.get('type')
                
                if not url:
                    errors.append(f'Episode {i}: Enclosure missing URL')
                elif not url.startswith(('http://', 'https://')):
                    errors.append(f'Episode {i}: Enclosure URL must be absolute')
                
                if not length:
                    errors.append(f'Episode {i}: Enclosure missing length')
                elif not length.isdigit():
                    errors.append(f'Episode {i}: Enclosure length must be numeric')
                
                if not media_type:
                    errors.append(f'Episode {i}: Enclosure missing type')
                elif media_type not in ['audio/mpeg', 'audio/mp4', 'audio/x-m4a']:
                    warnings.append(f'Episode {i}: Media type "{media_type}" may not be supported by all clients')
            
            # GUID validation
            guid_elem = episode.find('guid')
            if guid_elem is None:
                warnings.append(f'Episode {i}: Missing GUID (recommended for episode identification)')
            
            # Publication date validation
            pubdate_elem = episode.find('pubDate')
            if pubdate_elem is None:
                warnings.append(f'Episode {i}: Missing publication date')
            elif pubdate_elem.text:
                if not self._is_valid_rfc2822_date(pubdate_elem.text):
                    warnings.append(f'Episode {i}: Invalid publication date format')
            
            # iTunes duration validation
            duration_elem = episode.find('.//itunes:duration', self.itunes_ns)
            if duration_elem is not None and duration_elem.text:
                if not self._is_valid_duration(duration_elem.text):
                    warnings.append(f'Episode {i}: Invalid iTunes duration format')
        
        return {'errors': errors, 'warnings': warnings, 'recommendations': recommendations}
    
    def _validate_itunes_image(self, image_url: str) -> Dict[str, List[str]]:
        """Validate iTunes podcast image"""
        errors, warnings, recommendations = [], [], []
        
        try:
            # Check if it's a valid URL
            if not image_url.startswith(('http://', 'https://')):
                errors.append('iTunes image URL must be absolute')
                return {'errors': errors, 'warnings': warnings, 'recommendations': recommendations}
            
            # Try to fetch and validate image
            response = requests.head(image_url, timeout=10)
            if response.status_code != 200:
                warnings.append(f'iTunes image URL returned status {response.status_code}')
                return {'errors': errors, 'warnings': warnings, 'recommendations': recommendations}
            
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                errors.append('iTunes image URL does not point to an image')
                return {'errors': errors, 'warnings': warnings, 'recommendations': recommendations}
            
            # Download image to check dimensions (optional, can be resource intensive)
            if 'content-length' in response.headers:
                content_length = int(response.headers['content-length'])
                if content_length > 5 * 1024 * 1024:  # 5MB limit
                    warnings.append('iTunes image is very large, consider optimizing')
            
            recommendations.append('iTunes image should be between 1400x1400 and 3000x3000 pixels, square aspect ratio')
            
        except requests.RequestException:
            warnings.append('Could not fetch iTunes image for validation')
        
        return {'errors': errors, 'warnings': warnings, 'recommendations': recommendations}
    
    def _calculate_compliance_score(self, root: ET.Element, error_count: int, warning_count: int) -> float:
        """Calculate iTunes compliance score"""
        base_score = 100.0
        
        # Deduct points for errors and warnings
        base_score -= error_count * 10  # 10 points per error
        base_score -= warning_count * 2  # 2 points per warning
        
        # Bonus points for best practices
        episodes = root.findall('.//item')
        if len(episodes) >= 3:
            base_score += 5  # Bonus for having multiple episodes
        
        # Check for iTunes enhancements
        if root.find('.//itunes:summary', self.itunes_ns) is not None:
            base_score += 2
        
        if root.find('.//itunes:keywords', self.itunes_ns) is not None:
            base_score += 2
        
        return max(0.0, min(100.0, base_score))
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_valid_duration(self, duration: str) -> bool:
        """Validate iTunes duration format (HH:MM:SS, MM:SS, or seconds)"""
        patterns = [
            r'^\d+$',  # seconds
            r'^\d{1,2}:\d{2}$',  # MM:SS
            r'^\d{1,2}:\d{2}:\d{2}$'  # HH:MM:SS
        ]
        return any(re.match(pattern, duration) for pattern in patterns)
    
    def _is_valid_rfc2822_date(self, date_str: str) -> bool:
        """Basic RFC 2822 date validation"""
        try:
            # This is a simplified check - a full implementation would be more robust
            return len(date_str) > 20 and ('GMT' in date_str or '+' in date_str or '-' in date_str)
        except:
            return False
    
    def _load_language_codes(self) -> set:
        """Load valid ISO 639-1 language codes"""
        return {
            'aa', 'ab', 'ae', 'af', 'ak', 'am', 'an', 'ar', 'as', 'av', 'ay', 'az',
            'ba', 'be', 'bg', 'bh', 'bi', 'bm', 'bn', 'bo', 'br', 'bs',
            'ca', 'ce', 'ch', 'co', 'cr', 'cs', 'cu', 'cv', 'cy',
            'da', 'de', 'dv', 'dz',
            'ee', 'el', 'en', 'eo', 'es', 'et', 'eu',
            'fa', 'ff', 'fi', 'fj', 'fo', 'fr', 'fy',
            'ga', 'gd', 'gl', 'gn', 'gu', 'gv',
            'ha', 'he', 'hi', 'ho', 'hr', 'ht', 'hu', 'hy', 'hz',
            'ia', 'id', 'ie', 'ig', 'ii', 'ik', 'io', 'is', 'it', 'iu',
            'ja', 'jv',
            'ka', 'kg', 'ki', 'kj', 'kk', 'kl', 'km', 'kn', 'ko', 'kr', 'ks', 'ku', 'kv', 'kw', 'ky',
            'la', 'lb', 'lg', 'li', 'ln', 'lo', 'lt', 'lu', 'lv',
            'mg', 'mh', 'mi', 'mk', 'ml', 'mn', 'mr', 'ms', 'mt', 'my',
            'na', 'nb', 'nd', 'ne', 'ng', 'nl', 'nn', 'no', 'nr', 'nv', 'ny',
            'oc', 'oj', 'om', 'or', 'os',
            'pa', 'pi', 'pl', 'ps', 'pt',
            'qu',
            'rm', 'rn', 'ro', 'ru', 'rw',
            'sa', 'sc', 'sd', 'se', 'sg', 'si', 'sk', 'sl', 'sm', 'sn', 'so', 'sq', 'sr', 'ss', 'st', 'su', 'sv', 'sw',
            'ta', 'te', 'tg', 'th', 'ti', 'tk', 'tl', 'tn', 'to', 'tr', 'ts', 'tt', 'tw', 'ty',
            'ug', 'uk', 'ur', 'uz',
            've', 'vi', 'vo',
            'wa', 'wo',
            'xh',
            'yi', 'yo',
            'za', 'zh', 'zu'
        }
    
    def _load_itunes_categories(self) -> set:
        """Load valid iTunes podcast categories"""
        return {
            'Arts', 'Business', 'Comedy', 'Education', 'Fiction', 'Government', 
            'Health & Fitness', 'History', 'Kids & Family', 'Leisure', 'Music', 
            'News', 'Religion & Spirituality', 'Science', 'Society & Culture', 
            'Sports', 'Technology', 'True Crime', 'TV & Film'
        }
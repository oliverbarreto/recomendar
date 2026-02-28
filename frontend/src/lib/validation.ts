/**
 * Audio file validation utilities
 */

// Allowed audio file extensions and MIME types
const ALLOWED_EXTENSIONS = ['.mp3', '.m4a', '.wav', '.ogg', '.flac'];
const ALLOWED_MIME_TYPES = [
    'audio/mpeg',
    'audio/mp3',
    'audio/mp4',
    'audio/x-m4a',
    'audio/wav',
    'audio/x-wav',
    'audio/wave',
    'audio/ogg',
    'audio/flac',
    'audio/x-flac',
];

export interface AudioValidationResult {
    valid: boolean;
    error?: string;
    duration?: number;
}

/**
 * Validate an audio file
 * @param file - File to validate
 * @param maxSizeMB - Maximum file size in megabytes (default: 500)
 * @returns Validation result
 */
export async function validateAudioFile(
    file: File,
    maxSizeMB: number = 500
): Promise<AudioValidationResult> {
    // Check file size
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
        return {
            valid: false,
            error: `File size exceeds ${maxSizeMB}MB limit`,
        };
    }

    // Check file extension
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
        return {
            valid: false,
            error: `Invalid file type. Allowed: ${getAllowedExtensionsString()}`,
        };
    }

    // Check MIME type
    if (!ALLOWED_MIME_TYPES.includes(file.type)) {
        return {
            valid: false,
            error: `Invalid audio format. Expected audio file.`,
        };
    }

    // Try to extract duration using Web Audio API
    try {
        const duration = await getAudioDuration(file);
        return {
            valid: true,
            duration,
        };
    } catch (error) {
        // Duration extraction failed, but file is still valid
        return {
            valid: true,
        };
    }
}

/**
 * Get audio duration from file using Web Audio API
 * @param file - Audio file
 * @returns Duration in seconds
 */
export async function getAudioDuration(file: File): Promise<number> {
    return new Promise((resolve, reject) => {
        const audio = new Audio();
        const objectUrl = URL.createObjectURL(file);

        audio.addEventListener('loadedmetadata', () => {
            URL.revokeObjectURL(objectUrl);
            resolve(audio.duration);
        });

        audio.addEventListener('error', () => {
            URL.revokeObjectURL(objectUrl);
            reject(new Error('Failed to load audio metadata'));
        });

        audio.src = objectUrl;
    });
}

/**
 * Format file size in human-readable format
 * @param bytes - File size in bytes
 * @returns Formatted string (e.g., "2.5 MB")
 */
export function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Format duration in human-readable format
 * @param seconds - Duration in seconds
 * @returns Formatted string (e.g., "2:30" or "1:23:45")
 */
export function formatDuration(seconds: number): string {
    if (!seconds || seconds < 0) return '0:00';

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Get allowed file extensions as a comma-separated string
 * @returns String of allowed extensions (e.g., "MP3, M4A, WAV, OGG, FLAC")
 */
export function getAllowedExtensionsString(): string {
    return ALLOWED_EXTENSIONS.map(ext => ext.replace('.', '').toUpperCase()).join(', ');
}


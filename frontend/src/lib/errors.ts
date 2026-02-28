/**
 * Error handling utilities for API errors
 */

export interface UploadError {
    message: string
    code?: string
    details?: unknown
}

/**
 * Parse upload error from API response
 * @param error - Error object from API call
 * @returns Parsed upload error
 */
export function parseUploadError(error: unknown): UploadError {
    // Handle network errors
    if (error instanceof Error && (error.message === 'Failed to fetch' || error.message === 'Network request failed')) {
        return {
            message: 'Network error. Please check your connection and try again.',
            code: 'NETWORK_ERROR'
        }
    }

    // Handle HTTP errors with response data
    if (error && typeof error === 'object' && 'response' in error) {
        const errorResponse = error.response as { data?: unknown; status?: number }
        const { data, status } = errorResponse

        // Handle validation errors
        if (status === 400) {
            return {
                message: data.detail || 'Invalid request. Please check your input.',
                code: 'VALIDATION_ERROR',
                details: data
            }
        }

        // Handle authentication errors
        if (status === 401) {
            return {
                message: 'Authentication required. Please log in again.',
                code: 'AUTH_ERROR'
            }
        }

        // Handle authorization errors
        if (status === 403) {
            return {
                message: 'You do not have permission to perform this action.',
                code: 'PERMISSION_ERROR'
            }
        }

        // Handle not found errors
        if (status === 404) {
            return {
                message: 'Resource not found.',
                code: 'NOT_FOUND'
            }
        }

        // Handle file too large errors
        if (status === 413) {
            return {
                message: 'File is too large. Maximum size is 500MB.',
                code: 'FILE_TOO_LARGE'
            }
        }

        // Handle unsupported media type
        if (status === 415) {
            return {
                message: 'Unsupported file format. Please upload MP3, M4A, WAV, OGG, or FLAC.',
                code: 'UNSUPPORTED_FORMAT'
            }
        }

        // Handle duplicate episode errors
        if (status === 409) {
            const errorData = data && typeof data === 'object' && 'detail' in data ? data as { detail?: { error?: string } } : null
            return {
                message: errorData?.detail?.error || 'An episode with this title already exists in this channel.',
                code: 'DUPLICATE_EPISODE',
                details: data
            }
        }

        // Handle server errors
        if (status >= 500) {
            return {
                message: 'Server error. Please try again later.',
                code: 'SERVER_ERROR',
                details: data
            }
        }

        // Generic HTTP error
        const errorData = data && typeof data === 'object' ? data as { detail?: string; message?: string } : null
        return {
            message: errorData?.detail || errorData?.message || 'An error occurred',
            code: 'HTTP_ERROR',
            details: data
        }
    }

    // Handle generic errors
    return {
        message: error instanceof Error ? error.message : 'An unexpected error occurred',
        code: 'UNKNOWN_ERROR',
        details: error
    }
}

/**
 * Get user-friendly error message from upload error
 * @param error - Upload error object
 * @returns User-friendly error message
 */
export function getErrorMessage(error: UploadError): string {
    return error.message
}

/**
 * Check if error is a network error
 * @param error - Upload error object
 * @returns True if network error
 */
export function isNetworkError(error: UploadError): boolean {
    return error.code === 'NETWORK_ERROR'
}

/**
 * Check if error is an authentication error
 * @param error - Upload error object
 * @returns True if authentication error
 */
export function isAuthError(error: UploadError): boolean {
    return error.code === 'AUTH_ERROR'
}

/**
 * Check if error is a validation error
 * @param error - Upload error object
 * @returns True if validation error
 */
export function isValidationError(error: UploadError): boolean {
    return error.code === 'VALIDATION_ERROR'
}


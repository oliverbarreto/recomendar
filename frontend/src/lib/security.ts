/**
 * Frontend security utilities and validation
 */

// Input validation patterns
const VALIDATION_PATTERNS = {
  email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  url: /^https?:\/\/(?:[-\w.])+(?:\:[0-9]+)?(?:\/(?:[\w\/_.])*)?(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?$/,
  youtubeUrl: /^https?:\/\/(?:www\.)?(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})$/,
  alphanumeric: /^[a-zA-Z0-9\s]+$/,
  filename: /^[a-zA-Z0-9._\-\s]+$/,
  slug: /^[a-z0-9]+(?:-[a-z0-9]+)*$/,
}

// Malicious content patterns
const MALICIOUS_PATTERNS = [
  // XSS patterns
  /<script[^>]*>.*?<\/script>/gi,
  /javascript:/gi,
  /on\w+\s*=/gi,
  /<iframe[^>]*>.*?<\/iframe>/gi,
  /<object[^>]*>.*?<\/object>/gi,
  /<embed[^>]*>.*?<\/embed>/gi,
  
  // SQL injection patterns
  /(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)/gi,
  /(OR|AND)\s+\d+\s*=\s*\d+/gi,
  /[';]--/g,
  
  // Path traversal
  /\.\.\//g,
  /\.\.\\/g,
]

/**
 * Sanitize input by removing potentially dangerous content
 */
export const sanitizeInput = (input: string, maxLength = 1000): string => {
  if (typeof input !== 'string') {
    return String(input)
  }
  
  return input
    .replace(/[<>]/g, '') // Remove basic HTML brackets
    .replace(/javascript:/gi, '') // Remove javascript protocol
    .replace(/on\w+=/gi, '') // Remove event handlers
    .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '') // Remove control characters
    .trim()
    .slice(0, maxLength)
}

/**
 * Check if input contains malicious patterns
 */
export const containsMaliciousContent = (input: string): boolean => {
  if (typeof input !== 'string') {
    return false
  }
  
  return MALICIOUS_PATTERNS.some(pattern => pattern.test(input))
}

/**
 * Validate input against a pattern
 */
export const validatePattern = (input: string, pattern: keyof typeof VALIDATION_PATTERNS): boolean => {
  if (typeof input !== 'string') {
    return false
  }
  
  return VALIDATION_PATTERNS[pattern].test(input)
}

/**
 * Validate email address
 */
export const validateEmail = (email: string): boolean => {
  return validatePattern(email, 'email') && !containsMaliciousContent(email)
}

/**
 * Validate URL
 */
export const validateUrl = (url: string): boolean => {
  if (!validatePattern(url, 'url')) {
    return false
  }
  
  try {
    const parsed = new URL(url)
    // Only allow HTTP/HTTPS
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return false
    }
    
    // Block localhost and private IPs for external URLs
    const hostname = parsed.hostname.toLowerCase()
    if (hostname === 'localhost' || 
        hostname === '127.0.0.1' || 
        hostname.startsWith('192.168.') ||
        hostname.startsWith('10.') ||
        hostname.startsWith('172.')) {
      return false
    }
    
    return !containsMaliciousContent(url)
  } catch {
    return false
  }
}

/**
 * Validate YouTube URL specifically
 */
export const validateYouTubeUrl = (url: string): boolean => {
  return validatePattern(url, 'youtubeUrl') && !containsMaliciousContent(url)
}

/**
 * Validate filename for security
 */
export const validateFilename = (filename: string): boolean => {
  if (!validatePattern(filename, 'filename')) {
    return false
  }
  
  // Check for path traversal
  if (filename.includes('..') || filename.includes('/') || filename.includes('\\')) {
    return false
  }
  
  // Check for Windows reserved names
  const reservedNames = [
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
  ]
  
  if (reservedNames.includes(filename.toUpperCase())) {
    return false
  }
  
  return !containsMaliciousContent(filename)
}

/**
 * Validate channel/podcast name
 */
export const validateChannelName = (name: string): { isValid: boolean; errors: string[] } => {
  const errors: string[] = []
  
  if (!name || typeof name !== 'string') {
    errors.push('Channel name is required')
    return { isValid: false, errors }
  }
  
  const sanitized = name.trim()
  
  if (sanitized.length < 3) {
    errors.push('Channel name must be at least 3 characters long')
  }
  
  if (sanitized.length > 100) {
    errors.push('Channel name must be less than 100 characters')
  }
  
  if (containsMaliciousContent(sanitized)) {
    errors.push('Channel name contains invalid characters')
  }
  
  return { isValid: errors.length === 0, errors }
}

/**
 * Validate episode title
 */
export const validateEpisodeTitle = (title: string): { isValid: boolean; errors: string[] } => {
  const errors: string[] = []
  
  if (!title || typeof title !== 'string') {
    errors.push('Episode title is required')
    return { isValid: false, errors }
  }
  
  const sanitized = title.trim()
  
  if (sanitized.length < 5) {
    errors.push('Episode title must be at least 5 characters long')
  }
  
  if (sanitized.length > 200) {
    errors.push('Episode title must be less than 200 characters')
  }
  
  if (containsMaliciousContent(sanitized)) {
    errors.push('Episode title contains invalid characters')
  }
  
  return { isValid: errors.length === 0, errors }
}

/**
 * Validate description text
 */
export const validateDescription = (description: string, maxLength = 2000): { isValid: boolean; errors: string[] } => {
  const errors: string[] = []
  
  if (description && typeof description === 'string') {
    const sanitized = description.trim()
    
    if (sanitized.length > maxLength) {
      errors.push(`Description must be less than ${maxLength} characters`)
    }
    
    if (containsMaliciousContent(sanitized)) {
      errors.push('Description contains invalid characters')
    }
  }
  
  return { isValid: errors.length === 0, errors }
}

/**
 * Validate tag name
 */
export const validateTagName = (name: string): { isValid: boolean; errors: string[] } => {
  const errors: string[] = []
  
  if (!name || typeof name !== 'string') {
    errors.push('Tag name is required')
    return { isValid: false, errors }
  }
  
  const sanitized = name.trim()
  
  if (sanitized.length < 2) {
    errors.push('Tag name must be at least 2 characters long')
  }
  
  if (sanitized.length > 50) {
    errors.push('Tag name must be less than 50 characters')
  }
  
  if (!validatePattern(sanitized, 'alphanumeric')) {
    errors.push('Tag name can only contain letters, numbers, and spaces')
  }
  
  if (containsMaliciousContent(sanitized)) {
    errors.push('Tag name contains invalid characters')
  }
  
  return { isValid: errors.length === 0, errors }
}

/**
 * Secure form data before submission
 */
export const secureFormData = <T extends Record<string, any>>(data: T): T => {
  const secured = {} as T
  
  for (const [key, value] of Object.entries(data)) {
    if (typeof value === 'string') {
      secured[key as keyof T] = sanitizeInput(value) as T[keyof T]
    } else {
      secured[key as keyof T] = value
    }
  }
  
  return secured
}

/**
 * Content Security Policy helpers
 */
export const CSP_DIRECTIVES = {
  DEFAULT_SRC: "'self'",
  SCRIPT_SRC: "'self' 'unsafe-inline'",
  STYLE_SRC: "'self' 'unsafe-inline'",
  IMG_SRC: "'self' data: https:",
  FONT_SRC: "'self'",
  CONNECT_SRC: "'self'",
  FRAME_ANCESTORS: "'none'",
} as const

/**
 * Log security events (in development)
 */
export const logSecurityEvent = (event: string, details?: any): void => {
  if (process.env.NODE_ENV === 'development') {
    console.warn(`[Security] ${event}`, details)
  }
}
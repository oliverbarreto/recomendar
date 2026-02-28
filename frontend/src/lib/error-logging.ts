/**
 * Error logging and monitoring system for frontend
 */

export interface ErrorLogEntry {
  timestamp: string
  level: 'error' | 'warn' | 'info'
  message: string
  stack?: string
  url?: string
  userAgent?: string
  userId?: string
  sessionId?: string
  context?: Record<string, any>
}

export interface SecurityEvent {
  type: 'auth_failure' | 'rate_limit' | 'malicious_input' | 'api_error' | 'validation_error'
  timestamp: string
  details: Record<string, any>
  severity: 'low' | 'medium' | 'high' | 'critical'
}

class ErrorLogger {
  private logs: ErrorLogEntry[] = []
  private securityEvents: SecurityEvent[] = []
  private maxLogSize = 1000
  private sessionId: string

  constructor() {
    this.sessionId = this.generateSessionId()
    // Only set up global error handlers on the client side
    if (typeof window !== 'undefined') {
      this.setupGlobalErrorHandlers()
    }
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  private setupGlobalErrorHandlers(): void {
    // Only run this on the client side
    if (typeof window === 'undefined') {
      return
    }

    // Global error handler
    window.addEventListener('error', (event) => {
      this.logError('Global Error', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
      })
    })

    // Unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.logError('Unhandled Promise Rejection', {
        reason: event.reason,
        stack: event.reason?.stack,
      })
    })

    // React error boundary fallback
    if ((window as any).__REACT_ERROR_OVERLAY_GLOBAL_HOOK__) {
      const originalCaptureException = (window as any).__REACT_ERROR_OVERLAY_GLOBAL_HOOK__.captureException
      if (originalCaptureException) {
        (window as any).__REACT_ERROR_OVERLAY_GLOBAL_HOOK__.captureException = (error: Error) => {
          this.logError('React Error', {
            message: error.message,
            stack: error.stack,
          })
          return originalCaptureException(error)
        }
      }
    }
  }

  /**
   * Log a general error
   */
  logError(message: string, context?: Record<string, any>): void {
    this.addLog('error', message, context)
  }

  /**
   * Log a warning
   */
  logWarning(message: string, context?: Record<string, any>): void {
    this.addLog('warn', message, context)
  }

  /**
   * Log an info message
   */
  logInfo(message: string, context?: Record<string, any>): void {
    this.addLog('info', message, context)
  }

  /**
   * Log a security event
   */
  logSecurityEvent(type: SecurityEvent['type'], details: Record<string, any>, severity: SecurityEvent['severity'] = 'medium'): void {
    const event: SecurityEvent = {
      type,
      timestamp: new Date().toISOString(),
      details,
      severity,
    }

    this.securityEvents.push(event)

    // Also log as regular error for visibility
    this.logError(`Security Event: ${type}`, { ...details, severity })

    // Limit security events array size
    if (this.securityEvents.length > this.maxLogSize) {
      this.securityEvents.shift()
    }

    // In development, also console.warn
    if (process.env.NODE_ENV === 'development') {
      console.warn(`[SECURITY] ${type}:`, details)
    }
  }

  /**
   * Log API errors with security context
   */
  logApiError(endpoint: string, status: number, message: string, response?: unknown): void {
    const context = {
      endpoint,
      status,
      response,
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'SSR',
      url: typeof window !== 'undefined' ? window.location.href : 'SSR',
    }

    this.logError(`API Error: ${status} - ${message}`, context)

    // Log security-relevant API errors
    if (status === 401) {
      this.logSecurityEvent('auth_failure', context, 'high')
    } else if (status === 429) {
      this.logSecurityEvent('rate_limit', context, 'medium')
    } else if (status >= 400) {
      this.logSecurityEvent('api_error', context, 'low')
    }
  }

  /**
   * Log validation errors
   */
  logValidationError(field: string, value: unknown, errors: string[]): void {
    const context = {
      field,
      value: typeof value === 'string' ? value.substring(0, 100) : value, // Truncate sensitive data
      errors,
    }

    this.logWarning(`Validation Error: ${field}`, context)
    this.logSecurityEvent('validation_error', context, 'low')
  }

  /**
   * Log malicious input detection
   */
  logMaliciousInput(input: string, detected: string): void {
    const context = {
      input: input.substring(0, 200), // Limit logged input
      detected,
      url: typeof window !== 'undefined' ? window.location.href : 'SSR',
    }

    this.logError('Malicious Input Detected', context)
    this.logSecurityEvent('malicious_input', context, 'high')
  }

  private addLog(level: ErrorLogEntry['level'], message: string, context?: Record<string, any>): void {
    const entry: ErrorLogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      url: typeof window !== 'undefined' ? window.location.href : 'SSR',
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'SSR',
      sessionId: this.sessionId,
      context,
    }

    this.logs.push(entry)

    // Limit log size
    if (this.logs.length > this.maxLogSize) {
      this.logs.shift()
    }

    // Console output in development
    if (process.env.NODE_ENV === 'development') {
      const consoleMethod = level === 'error' ? console.error : level === 'warn' ? console.warn : console.log
      consoleMethod(`[${level.toUpperCase()}] ${message}`, context)
    }
  }

  /**
   * Get recent logs
   */
  getLogs(limit = 50): ErrorLogEntry[] {
    return this.logs.slice(-limit)
  }

  /**
   * Get recent security events
   */
  getSecurityEvents(limit = 50): SecurityEvent[] {
    return this.securityEvents.slice(-limit)
  }

  /**
   * Clear all logs
   */
  clearLogs(): void {
    this.logs = []
    this.securityEvents = []
  }

  /**
   * Export logs for debugging
   */
  exportLogs(): string {
    return JSON.stringify({
      sessionId: this.sessionId,
      timestamp: new Date().toISOString(),
      logs: this.logs,
      securityEvents: this.securityEvents,
    }, null, 2)
  }

  /**
   * Get error statistics
   */
  getErrorStats(): {
    totalErrors: number
    totalWarnings: number
    totalSecurityEvents: number
    recentErrors: number
    criticalSecurityEvents: number
  } {
    const now = Date.now()
    const oneHourAgo = now - (60 * 60 * 1000)

    const recentErrors = this.logs.filter(log =>
      log.level === 'error' &&
      Date.parse(log.timestamp) > oneHourAgo
    ).length

    const criticalSecurityEvents = this.securityEvents.filter(event =>
      event.severity === 'critical'
    ).length

    return {
      totalErrors: this.logs.filter(log => log.level === 'error').length,
      totalWarnings: this.logs.filter(log => log.level === 'warn').length,
      totalSecurityEvents: this.securityEvents.length,
      recentErrors,
      criticalSecurityEvents,
    }
  }
}

// Global error logger instance (lazy initialization for SSR compatibility)
let globalErrorLogger: ErrorLogger | null = null

export const errorLogger = {
  get instance(): ErrorLogger {
    if (!globalErrorLogger && typeof window !== 'undefined') {
      globalErrorLogger = new ErrorLogger()
    }
    return globalErrorLogger!
  },

  // Provide safe methods that work during SSR
  logError: (message: string, context?: Record<string, any>) => {
    if (typeof window !== 'undefined') {
      errorLogger.instance.logError(message, context)
    }
  },

  logWarning: (message: string, context?: Record<string, any>) => {
    if (typeof window !== 'undefined') {
      errorLogger.instance.logWarning(message, context)
    }
  },

  logInfo: (message: string, context?: Record<string, any>) => {
    if (typeof window !== 'undefined') {
      errorLogger.instance.logInfo(message, context)
    }
  },

  logApiError: (endpoint: string, status: number, message: string, response?: unknown) => {
    if (typeof window !== 'undefined') {
      errorLogger.instance.logApiError(endpoint, status, message, response)
    }
  },

  logValidationError: (field: string, value: unknown, errors: string[]) => {
    if (typeof window !== 'undefined') {
      errorLogger.instance.logValidationError(field, value, errors)
    }
  },

  logSecurityEvent: (type: SecurityEvent['type'], details: Record<string, any>, severity: SecurityEvent['severity'] = 'medium') => {
    if (typeof window !== 'undefined') {
      errorLogger.instance.logSecurityEvent(type, details, severity)
    }
  }
}

/**
 * React Error Boundary component
 */
export class ErrorBoundary extends Error {
  constructor(message: string, public originalError?: Error) {
    super(message)
    this.name = 'ErrorBoundary'
  }
}

/**
 * Utility to wrap async functions with error logging
 */
export const withErrorLogging = <T extends (...args: unknown[]) => Promise<unknown>>(
  fn: T,
  context?: string
): T => {
  return (async (...args: unknown[]) => {
    try {
      return await fn(...args)
    } catch (error) {
      const message = `Error in ${context || fn.name}: ${error instanceof Error ? error.message : 'Unknown error'}`
      errorLogger.logError(message, {
        function: context || fn.name,
        args: args.slice(0, 3), // Limit args to prevent sensitive data logging
        error: error instanceof Error ? error.stack : error,
      })
      throw error
    }
  }) as T
}

/**
 * Hook for React components to log errors
 */
export const useErrorLogger = () => {
  return {
    logError: errorLogger.logError,
    logWarning: errorLogger.logWarning,
    logInfo: errorLogger.logInfo,
    logApiError: errorLogger.logApiError,
    logValidationError: errorLogger.logValidationError,
    logSecurityEvent: errorLogger.logSecurityEvent,
  }
}
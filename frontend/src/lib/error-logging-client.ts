'use client'

/**
 * Client-side error logging and monitoring system for frontend
 * This module is designed to run only in the browser environment
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

class ClientErrorLogger {
  private logs: ErrorLogEntry[] = []
  private securityEvents: SecurityEvent[] = []
  private maxLogSize = 1000
  private sessionId: string

  constructor() {
    this.sessionId = this.generateSessionId()
    this.setupGlobalErrorHandlers()
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  private setupGlobalErrorHandlers(): void {
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
    this.logError(`Security Event: ${type}`, { ...details, severity })

    if (this.securityEvents.length > this.maxLogSize) {
      this.securityEvents.shift()
    }

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
      userAgent: navigator.userAgent,
      url: window.location.href,
    }

    this.logError(`API Error: ${status} - ${message}`, context)

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
      value: typeof value === 'string' ? value.substring(0, 100) : value,
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
      input: input.substring(0, 200),
      detected,
      url: window.location.href,
    }

    this.logError('Malicious Input Detected', context)
    this.logSecurityEvent('malicious_input', context, 'high')
  }

  private addLog(level: ErrorLogEntry['level'], message: string, context?: Record<string, any>): void {
    const entry: ErrorLogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      url: window.location.href,
      userAgent: navigator.userAgent,
      sessionId: this.sessionId,
      context,
    }

    this.logs.push(entry)

    if (this.logs.length > this.maxLogSize) {
      this.logs.shift()
    }

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
}

// Global error logger instance (client-side only)
let clientErrorLogger: ClientErrorLogger | null = null

export const getErrorLogger = (): ClientErrorLogger => {
  if (!clientErrorLogger) {
    clientErrorLogger = new ClientErrorLogger()
  }
  return clientErrorLogger
}

/**
 * Hook for React components to log errors (client-side only)
 */
export const useErrorLogger = () => {
  const logger = getErrorLogger()

  return {
    logError: logger.logError.bind(logger),
    logWarning: logger.logWarning.bind(logger),
    logInfo: logger.logInfo.bind(logger),
    logApiError: logger.logApiError.bind(logger),
    logValidationError: logger.logValidationError.bind(logger),
    logSecurityEvent: logger.logSecurityEvent.bind(logger),
  }
}
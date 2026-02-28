/**
 * Color generation utilities for creating vivid, aesthetically pleasing gradients
 * for uploaded episode backgrounds
 */

export interface GradientColors {
    start: string
    middle?: string
    end: string
}

/**
 * Predefined color palettes for generating beautiful gradients
 * Each palette contains 2-3 colors that work well together
 */
const GRADIENT_PALETTES: string[][] = [
    // Warm palettes
    ['#FF6B6B', '#4ECDC4', '#45B7D1'], // Coral, Teal, Blue
    ['#FF8A80', '#FFD54F', '#81C784'], // Coral, Yellow, Green
    ['#E57373', '#FFB74D', '#81C784'], // Red, Orange, Green
    ['#F48FB1', '#CE93D8', '#90CAF9'], // Pink, Purple, Blue

    // Cool palettes
    ['#42A5F5', '#26C6DA', '#4DB6AC'], // Blue, Cyan, Teal
    ['#7986CB', '#BA68C8', '#EF5350'], // Indigo, Purple, Red
    ['#5C6BC0', '#42A5F5', '#26A69A'], // Blue variations
    ['#7E57C2', '#5E35B1', '#3949AB'], // Purple variations

    // Nature-inspired
    ['#66BB6A', '#4CAF50', '#2E7D32'], // Green variations
    ['#FFA726', '#FF7043', '#D84315'], // Orange variations
    ['#AB47BC', '#8E24AA', '#6A1B9A'], // Purple variations
    ['#29B6F6', '#0277BD', '#01579B'], // Blue variations

    // Vibrant palettes
    ['#FF5722', '#FF9800', '#FFC107'], // Orange, Amber
    ['#E91E63', '#9C27B0', '#673AB7'], // Pink, Purple
    ['#3F51B5', '#2196F3', '#03A9F4'], // Indigo, Blue, Cyan
    ['#009688', '#4CAF50', '#8BC34A'], // Teal, Green, Light Green
]

/**
 * Generate a deterministic hash from a string (episode ID)
 * Used to ensure the same episode always gets the same colors
 */
function hashString(str: string): number {
    let hash = 0
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i)
        hash = ((hash << 5) - hash) + char
        hash = hash & hash // Convert to 32-bit integer
    }
    return Math.abs(hash)
}

/**
 * Generate gradient colors for an uploaded episode based on its video ID
 * Uses the episode ID as a seed to ensure consistent colors across renders
 *
 * @param videoId - The episode's video ID (should start with 'up_')
 * @returns GradientColors object with start, middle (optional), and end colors
 */
export function generateEpisodeGradient(videoId: string): GradientColors {
    if (!videoId || !videoId.startsWith('up_')) {
        // Fallback for invalid video IDs
        return {
            start: '#6366F1',
            end: '#8B5CF6'
        }
    }

    // Use video ID as seed for deterministic color selection
    const hash = hashString(videoId)
    const paletteIndex = hash % GRADIENT_PALETTES.length
    const selectedPalette = GRADIENT_PALETTES[paletteIndex]

    if (selectedPalette.length === 2) {
        return {
            start: selectedPalette[0],
            end: selectedPalette[1]
        }
    } else {
        // Use 3-color palette
        return {
            start: selectedPalette[0],
            middle: selectedPalette[1],
            end: selectedPalette[2]
        }
    }
}

/**
 * Generate CSS gradient string from gradient colors
 */
export function generateGradientCSS(colors: GradientColors): string {
    if (colors.middle) {
        return `linear-gradient(135deg, ${colors.start}, ${colors.middle}, ${colors.end})`
    } else {
        return `linear-gradient(135deg, ${colors.start}, ${colors.end})`
    }
}

/**
 * Generate a complete gradient style object for React inline styles
 */
export function generateGradientStyle(videoId: string): React.CSSProperties {
    const colors = generateEpisodeGradient(videoId)
    return {
        background: generateGradientCSS(colors)
    }
}

/**
 * Check if two colors have sufficient contrast for text readability
 * Uses a simple luminance calculation for basic contrast checking
 */
export function hasGoodContrast(backgroundColor: string, textColor: string = '#FFFFFF'): boolean {
    const getLuminance = (hex: string): number => {
        const rgb = parseInt(hex.slice(1), 16)
        const r = (rgb >> 16) & 0xff
        const g = (rgb >> 8) & 0xff
        const b = (rgb >> 0) & 0xff

        // Convert to linear RGB
        const toLinear = (val: number) => val <= 0.03928 ? val / 12.92 : Math.pow((val + 0.055) / 1.055, 2.4)

        const rLinear = toLinear(r / 255)
        const gLinear = toLinear(g / 255)
        const bLinear = toLinear(b / 255)

        // Calculate relative luminance
        return 0.2126 * rLinear + 0.7152 * gLinear + 0.0722 * bLinear
    }

    const bgLuminance = getLuminance(backgroundColor)
    const textLuminance = getLuminance(textColor)

    const ratio = (Math.max(bgLuminance, textLuminance) + 0.05) / (Math.min(bgLuminance, textLuminance) + 0.05)

    return ratio >= 4.5 // WCAG AA standard for normal text
}

/**
 * Get the most appropriate text color for a gradient background
 * Analyzes the gradient colors to determine if white or black text would be more readable
 */
export function getOptimalTextColor(colors: GradientColors): string {
    // Calculate average luminance of all colors in the gradient
    const getLuminance = (hex: string): number => {
        const rgb = parseInt(hex.slice(1), 16)
        const r = (rgb >> 16) & 0xff
        const g = (rgb >> 8) & 0xff
        const b = (rgb >> 0) & 0xff

        const toLinear = (val: number) => val <= 0.03928 ? val / 12.92 : Math.pow((val + 0.055) / 1.055, 2.4)

        const rLinear = toLinear(r / 255)
        const gLinear = toLinear(g / 255)
        const bLinear = toLinear(b / 255)

        return 0.2126 * rLinear + 0.7152 * gLinear + 0.0722 * bLinear
    }

    const allColors = [colors.start]
    if (colors.middle) allColors.push(colors.middle)
    allColors.push(colors.end)

    const avgLuminance = allColors.reduce((sum, color) => sum + getLuminance(color), 0) / allColors.length

    // Return white text for dark backgrounds, black text for light backgrounds
    return avgLuminance < 0.5 ? '#FFFFFF' : '#000000'
}

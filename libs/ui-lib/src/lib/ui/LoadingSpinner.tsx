/**
 * LoadingSpinner — full-screen or inline centered spinner with optional message.
 */
export interface LoadingSpinnerProps {
    message?: string;
    /** When true, wraps in a full min-h-screen centered container */
    fullScreen?: boolean;
    size?: 'sm' | 'md' | 'lg';
}

const SIZE_MAP = {
    sm: 'w-5 h-5',
    md: 'w-8 h-8',
    lg: 'w-10 h-10',
} as const;

// Inline SVG spinner to avoid depending on lucide-react inside ui-lib
function SpinnerIcon({ className }: { className: string }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            className={`animate-spin text-primary ${className}`}
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
        >
            <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
            />
            <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
        </svg>
    );
}

export function LoadingSpinner({ message, fullScreen = false, size = 'lg' }: LoadingSpinnerProps) {
    const inner = (
        <div className="flex flex-col items-center gap-4">
            <SpinnerIcon className={SIZE_MAP[size]} />
            {message && <p className="text-muted-foreground font-medium">{message}</p>}
        </div>
    );

    if (fullScreen) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                {inner}
            </div>
        );
    }

    return (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
            {inner}
        </div>
    );
}

export default LoadingSpinner;

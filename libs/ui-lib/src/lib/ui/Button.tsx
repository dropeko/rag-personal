import type { ButtonHTMLAttributes, ReactNode } from 'react';

/**
 * Button — ISQ-styled button with primary and ghost variants.
 */
export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'ghost';
    loading?: boolean;
    children: ReactNode;
}

function SpinnerIcon() {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            className="animate-spin w-5 h-5"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
        >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
    );
}

const VARIANT_CLASSES = {
    primary:
        'bg-primary hover:bg-primary-light text-white shadow-[0_0_20px_rgba(214,0,0,0.4)] hover:shadow-[0_0_30px_rgba(214,0,0,0.6)]',
    ghost:
        'bg-transparent hover:bg-primary/10 text-primary border border-primary/30',
} as const;

export function Button({
    variant = 'primary',
    loading = false,
    disabled,
    children,
    className = '',
    ...props
}: ButtonProps) {
    return (
        <button
            disabled={loading || disabled}
            className={`
                inline-flex items-center justify-center gap-2
                px-6 py-3 rounded-xl font-semibold
                transition-all duration-200
                disabled:opacity-70 disabled:cursor-not-allowed
                ${VARIANT_CLASSES[variant]}
                ${className}
            `}
            {...props}
        >
            {loading ? <SpinnerIcon /> : children}
        </button>
    );
}

export default Button;

/**
 * Badge — pill tag with ISQ border accent.
 * Use to display metadata labels (client, unit, category, etc.).
 */
export interface BadgeProps {
    label?: string;
    className?: string;
}

export function Badge({ label, className = '' }: BadgeProps) {
    if (!label) return null;
    return (
        <span
            className={`inline-flex items-center rounded-full text-xs font-medium bg-secondary text-foreground border border-primary  px-2 py-1 /20 ${className}`}
        >
            {label}
        </span>
    );
}

export default Badge;

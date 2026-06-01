import type { ReactNode } from 'react';

/**
 * InfoItem — displays an icon + label + value cell.
 * Used in report header info strips (date, client, unit, tag, etc.).
 */
export interface InfoItemProps {
    icon: ReactNode;
    label: string;
    value?: string;
}

export function InfoItem({ icon, label, value }: InfoItemProps) {
    if (!value) return null;
    return (
        <div className="p-6 flex flex-col gap-1 hover:bg-primary/5 transition-colors duration-200">
            <div className="flex items-center gap-2 text-primary/60 text-xs font-semibold uppercase tracking-wider mb-1">
                {icon}
                {label}
            </div>
            <span className="font-medium text-foreground truncate" title={value}>
                {value}
            </span>
        </div>
    );
}

export default InfoItem;

import React from 'react';

export const inputCls = "w-full bg-secondary/50 border border-border rounded-xl px-4 py-3 text-foreground placeholder:text-muted-foreground/60 outline-none transition-all duration-200 glow-ring focus:glow-ring-focus text-sm";

export function FieldGroup({ icon: Icon, label, children }: {
    icon: React.ElementType;
    label: string;
    children: React.ReactNode;
}) {
    return (
        <div className="space-y-1.5 w-full">
            <label className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                <Icon className="w-3.5 h-3.5 text-primary" />
                {label}
            </label>
            {children}
        </div>
    );
}

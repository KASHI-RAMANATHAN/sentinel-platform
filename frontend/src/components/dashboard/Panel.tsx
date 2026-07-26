import type { ReactNode } from 'react';
import { MoreHorizontal } from 'lucide-react';

interface PanelProps {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
  variant?: 'default' | 'strong';
}

export default function Panel({
  title,
  subtitle,
  icon,
  action,
  children,
  className = '',
  bodyClassName = 'p-6',
  variant = 'default',
}: PanelProps) {
  return (
    <div
      className={`relative rounded-none border border-black/20 bg-white dark:border-white/20 dark:bg-black transition-colors ${className}`}
    >
      <div className="flex items-center justify-between gap-3 border-b border-black/10 px-6 py-4 dark:border-white/10">
        <div className="flex min-w-0 items-center gap-3">
          {icon && (
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-black/10 bg-transparent text-black dark:border-white/10 dark:text-white">
              {icon}
            </div>
          )}
          <div className="min-w-0">
            <h3 className="text-[15px] font-semibold tracking-tight text-black dark:text-white truncate">
              {title}
            </h3>
            {subtitle && (
              <p className="mt-0.5 text-xs text-black/60 dark:text-white/60 truncate">{subtitle}</p>
            )}
          </div>
        </div>
        {action ?? (
          <button className="flex h-8 w-8 items-center justify-center rounded-none text-black/40 transition-colors hover:bg-black/5 hover:text-black dark:text-white/40 dark:hover:bg-white/10 dark:hover:text-white">
            <MoreHorizontal className="h-4 w-4" />
          </button>
        )}
      </div>
      <div className={bodyClassName}>{children}</div>
    </div>
  );
}

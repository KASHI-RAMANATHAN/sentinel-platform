import type { Severity, AlertStatus } from '@/types';

export const severityStyles: Record<Severity, string> = {
  critical: 'border-black bg-black text-white dark:border-white dark:bg-white dark:text-black',
  high: 'border-black/60 bg-transparent text-black/80 dark:border-white/60 dark:text-white/80',
  medium: 'border-black/40 bg-transparent text-black/60 dark:border-white/40 dark:text-white/60',
  low: 'border-black/20 bg-transparent text-black/40 dark:border-white/20 dark:text-white/40',
  resolved: 'border-black/10 bg-transparent text-black/40 dark:border-white/10 dark:text-white/40',
};

export const statusStyles: Record<AlertStatus, string> = {
  investigating: 'border-black bg-black text-white dark:border-white dark:bg-white dark:text-black',
  open: 'border-black/60 bg-transparent text-black dark:border-white/60 dark:text-white',
  resolved: 'border-black/20 bg-transparent text-black/40 dark:border-white/20 dark:text-white/40',
  blocked: 'border-black/10 bg-black/5 text-black/40 dark:border-white/10 dark:bg-white/5 dark:text-white/40',
};

interface BadgeProps {
  variant: 'severity' | 'status';
  value: Severity | AlertStatus;
}

export default function Badge({ variant, value }: BadgeProps) {
  const styles =
    variant === 'severity'
      ? severityStyles[value as Severity]
      : statusStyles[value as AlertStatus];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-none border px-2.5 py-0.5 text-[10px] font-mono font-semibold uppercase tracking-wider ${styles}`}
    >
      <span className="h-1.5 w-1.5 rounded-none bg-current" />
      {value}
    </span>
  );
}

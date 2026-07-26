import {
  Activity,
  ShieldAlert,
  Gauge,
  Server,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { Kpi } from '@/types';

interface KpiCardProps {
  kpi: Kpi;
}

const iconMap: Record<Kpi['icon'], LucideIcon> = {
  sessions: Activity,
  threats: ShieldAlert,
  risk: Gauge,
  devices: Server,
};

const accentMap: Record<Kpi['icon'], { text: string; iconBg: string }> = {
  sessions: { text: 'text-black dark:text-white', iconBg: 'border-black/20 dark:border-white/20' },
  threats: { text: 'text-black dark:text-white', iconBg: 'border-black/20 dark:border-white/20' },
  risk: { text: 'text-black dark:text-white', iconBg: 'border-black/20 dark:border-white/20' },
  devices: { text: 'text-black dark:text-white', iconBg: 'border-black/20 dark:border-white/20' },
};

export default function KpiCard({ kpi }: KpiCardProps) {
  const Icon = iconMap[kpi.icon];
  const accent = accentMap[kpi.icon];
  const TrendIcon = kpi.trend === 'up' ? ArrowUpRight : ArrowDownRight;

  return (
    <div className="group relative overflow-hidden rounded-none border border-black/20 bg-white dark:border-white/20 dark:bg-black transition-colors hover:border-black dark:hover:border-white">
      <div className="relative p-6">
        <div className="flex items-start justify-between">
          <div
            className={`flex h-11 w-11 items-center justify-center rounded-none border ${accent.iconBg} ${accent.text}`}
          >
            <Icon className="h-5 w-5" strokeWidth={1.5} />
          </div>
          <span
            className={`inline-flex items-center gap-1 rounded-none border px-2.5 py-1 text-[10px] font-mono font-semibold uppercase tracking-wider ${
              kpi.positive
                ? 'border-black/20 text-black dark:border-white/20 dark:text-white'
                : 'border-black bg-black text-white dark:border-white dark:bg-white dark:text-black'
            }`}
          >
            <TrendIcon className="h-3.5 w-3.5" />
            {kpi.delta}
          </span>
        </div>

        <div className="mt-5">
          <p className="text-[10px] font-mono font-semibold uppercase tracking-wider text-black/60 dark:text-white/60">{kpi.label}</p>
          <p className="mt-1.5 text-[34px] font-bold tracking-tight text-black dark:text-white">
            {kpi.value}
          </p>
        </div>
      </div>
    </div>
  );
}

import { useEffect, useState } from 'react';
import {
  X,
  ArrowRight,
  Shield,
  Globe,
  Clock,
  Activity,
  Network,
  Crosshair,
  CheckCircle2,
  MapPin,
  Monitor,
  Sparkles,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { Alert } from '@/types';
import { AlertsAPI, type AlertDetail } from '@/api/alerts';
import Badge from './Badge';
import { AlertDetailsSkeleton } from './Skeleton';

interface AlertDetailsPanelProps {
  alert: Alert | null;
  loading?: boolean;
  onClose: () => void;
  onInvestigate?: (id: string) => void;
  onResolve?: (id: string) => void;
}

function riskColor(score: number) {
  if (score >= 80) return { text: 'text-black dark:text-white', bar: 'bg-black dark:bg-white' };
  if (score >= 60) return { text: 'text-black/80 dark:text-white/80', bar: 'bg-black/80 dark:bg-white/80' };
  if (score >= 40) return { text: 'text-black/60 dark:text-white/60', bar: 'bg-black/60 dark:bg-white/60' };
  return { text: 'text-black/40 dark:text-white/40', bar: 'bg-black/40 dark:bg-white/40' };
}

export default function AlertDetailsPanel({
  alert,
  loading = false,
  onClose,
  onInvestigate,
  onResolve
}: AlertDetailsPanelProps) {
  const [detail, setDetail] = useState<AlertDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!alert?.id) {
      setDetail(null);
      return;
    }

    let isMounted = true;
    const fetchDetail = async () => {
      setDetailLoading(true);
      setError(null);
      try {
        const data = await AlertsAPI.getAlertById(alert.id);
        if (isMounted) setDetail(data);
      } catch (err) {
        if (isMounted) setError('Failed to load alert details.');
      } finally {
        if (isMounted) setDetailLoading(false);
      }
    };
    fetchDetail();

    return () => {
      isMounted = false;
    };
  }, [alert?.id]);

  if (loading || detailLoading) {
    return <AlertDetailsSkeleton />;
  }

  if (!alert) {
    return (
      <div className="flex h-full flex-col items-center justify-center rounded-none border border-black/20 bg-white p-8 text-center dark:border-white/20 dark:bg-black">
        <div className="flex h-14 w-14 items-center justify-center rounded-none border border-black/20 text-black/40 dark:border-white/20 dark:text-white/40">
          <Shield className="h-7 w-7" />
        </div>
        <p className="mt-4 text-sm text-black dark:text-white">No alert selected</p>
        <p className="mt-1.5 text-xs text-black/60 dark:text-white/60">
          Select an alert from the table to view its details.
        </p>
      </div>
    );
  }

  const fields: { icon: LucideIcon; label: string; value: string; mono?: boolean }[] = [
    { icon: Globe, label: 'Source IP', value: detail?.source_ip || alert.source || 'Unknown', mono: true },
    { 
      icon: MapPin, 
      label: 'Geo Location', 
      value: detail?.geo_location 
        ? [detail.geo_location.city, detail.geo_location.country].filter(Boolean).join(', ') || 'Unknown' 
        : 'Loading...' 
    },
    { 
      icon: Monitor, 
      label: 'Device', 
      value: detail?.device 
        ? [detail.device.os, detail.device.browser].filter(Boolean).join(' ') || 'Unknown' 
        : 'Loading...' 
    },
    { icon: Activity, label: 'Attack Type', value: detail?.attack_type || alert.category || 'Unknown' },
    { 
      icon: Clock, 
      label: 'Timestamp', 
      value: detail ? new Date(detail.timestamp).toLocaleString() : alert.timestamp, 
      mono: true 
    },
  ];

  const currentRisk = alert.riskScore;
  const currentSeverity = alert.severity;
  const currentStatus = alert.status;

  const risk = riskColor(currentRisk);

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-none border border-black/20 bg-white animate-slide-in dark:border-white/20 dark:bg-black">
      <div className="flex items-center justify-between gap-3 border-b border-black/10 px-6 py-4 dark:border-white/10">
        <div className="min-w-0">
          <span className="font-mono text-xs text-black/40 dark:text-white/40">{alert.id}</span>
          <h3 className="mt-1 truncate text-[15px] font-semibold tracking-tight text-black dark:text-white">
            {detail ? `Detected ${detail.attack_type}` : alert.title}
          </h3>
        </div>
        <button
          onClick={onClose}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-none text-black/40 transition-colors hover:bg-black/5 hover:text-black dark:text-white/40 dark:hover:bg-white/10 dark:hover:text-white"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-5">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="severity" value={currentSeverity} />
          <Badge variant="status" value={currentStatus} />
        </div>

        <div className="mt-4 rounded-none border border-black/10 bg-transparent p-4 dark:border-white/10">
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase tracking-wider text-black/40 dark:text-white/40">
              Risk Score
            </span>
            <span className={`font-mono text-2xl font-bold ${risk.text}`}>
              {currentRisk}
            </span>
          </div>
          <div className="mt-3 h-2 overflow-hidden rounded-none border border-black/20 bg-transparent dark:border-white/20">
            <div
              className={`h-full transition-all ${risk.bar}`}
              style={{ width: `${currentRisk}%` }}
            />
          </div>
        </div>

        <div className="mt-4 space-y-2.5">
          {fields.map((field) => (
            <div
              key={field.label}
              className="flex items-center gap-3 rounded-none border border-black/10 bg-transparent px-3.5 py-3 dark:border-white/10"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-black/10 bg-transparent text-black dark:border-white/10 dark:text-white">
                <field.icon className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-[11px] uppercase tracking-wider text-black/40 dark:text-white/40">
                  {field.label}
                </p>
                <p
                  className={`truncate text-sm text-black dark:text-white ${
                    field.mono ? 'font-mono' : ''
                  }`}
                >
                  {field.value}
                </p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-5">
          <p className="text-[10px] font-mono font-semibold uppercase tracking-wider text-black/40 dark:text-white/40">
            Description
          </p>
          {error ? (
            <p className="mt-2 text-sm text-black dark:text-white">{error}</p>
          ) : (
            <p className="mt-2 text-sm leading-relaxed text-black/80 dark:text-white/80">
              {alert.description}
            </p>
          )}
        </div>

        {detail?.shap_explanation && (
          <div className="mt-5">
            <p className="text-[10px] font-mono font-semibold uppercase tracking-wider text-black/40 dark:text-white/40">
              Model Analysis
            </p>
            <div className="mt-2 space-y-3 rounded-none border border-black/10 bg-transparent p-4 dark:border-white/10">
              <p className="text-sm leading-relaxed text-black/80 dark:text-white/80">
                {detail.shap_explanation.summary}
              </p>
              {detail.shap_explanation.top_features && detail.shap_explanation.top_features.length > 0 && (
                <div className="space-y-1.5 border-t border-black/10 pt-3 dark:border-white/10">
                  {detail.shap_explanation.top_features.map((f, i) => (
                    <div key={i} className="flex items-center justify-between text-xs">
                      <span className="font-medium text-black/80 dark:text-white/80">{f.feature}</span>
                      <span className="font-mono text-black/60 dark:text-white/60">{f.shap_value.toFixed(4)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {detail?.recommended_action && (
          <div className="mt-5">
            <p className="text-[10px] font-mono font-semibold uppercase tracking-wider text-black/40 dark:text-white/40">
              Recommended Action
            </p>
            <div className="mt-2 rounded-none border border-black p-4 dark:border-white">
              <p className="text-sm leading-relaxed text-black dark:text-white font-mono">
                {detail.recommended_action}
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-black/10 p-5 dark:border-white/10">
        <div className="flex gap-2.5">
          <button 
            onClick={() => {
              if (alert?.id && onInvestigate) onInvestigate(alert.id);
            }}
            className="flex flex-1 items-center justify-center gap-2 rounded-none border border-black bg-black py-2.5 text-sm font-medium text-white transition-colors hover:bg-white hover:text-black dark:border-white dark:bg-white dark:text-black dark:hover:bg-black dark:hover:text-white"
          >
            <Crosshair className="h-4 w-4" />
            Investigate
          </button>
          <button 
            onClick={() => {
              if (alert?.id && onResolve) onResolve(alert.id);
            }}
            className="flex flex-1 items-center justify-center gap-2 rounded-none border border-black bg-transparent py-2.5 text-sm font-medium text-black transition-colors hover:bg-black hover:text-white dark:border-white dark:text-white dark:hover:bg-white dark:hover:text-black"
          >
            <CheckCircle2 className="h-4 w-4" />
            Resolve
          </button>
        </div>
      </div>
    </div>
  );
}

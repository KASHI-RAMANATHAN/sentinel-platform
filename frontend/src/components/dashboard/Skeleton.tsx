import type { ReactNode } from 'react';

interface SkeletonProps {
  className?: string;
  rounded?: string;
}

export function Skeleton({
  className = '',
  rounded = 'rounded-lg',
}: SkeletonProps) {
  return (
    <div
      className={`animate-shimmer ${rounded} ${className}`}
      aria-hidden="true"
    />
  );
}

interface SkeletonTextProps {
  lines?: number;
  className?: string;
  lineHeight?: string;
}

export function SkeletonText({
  lines = 3,
  className = '',
  lineHeight = 'h-3',
}: SkeletonTextProps) {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={`${lineHeight} ${i === lines - 1 ? 'w-2/3' : 'w-full'}`}
        />
      ))}
    </div>
  );
}

export function SkeletonCard({ children }: { children?: ReactNode }) {
  return (
    <div className="rounded-3xl glass p-6">
      {children ?? (
        <>
          <div className="flex items-start justify-between">
            <Skeleton className="h-11 w-11 rounded-2xl" />
            <Skeleton className="h-6 w-16 rounded-full" />
          </div>
          <Skeleton className="mt-5 h-3 w-24" />
          <Skeleton className="mt-2 h-8 w-32 rounded-md" />
        </>
      )}
    </div>
  );
}

export function KpiCardSkeleton() {
  return (
    <div className="rounded-3xl glass p-6">
      <div className="flex items-start justify-between">
        <Skeleton className="h-11 w-11 rounded-2xl" />
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
      <Skeleton className="mt-5 h-3 w-24" />
      <Skeleton className="mt-2.5 h-8 w-32 rounded-md" />
    </div>
  );
}

export function ChartSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-3 w-40" />
        <Skeleton className="h-3 w-24" />
      </div>
      <Skeleton className="h-[220px] w-full" rounded="rounded-2xl" />
      <div className="flex justify-between">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-2 w-8" />
        ))}
      </div>
    </div>
  );
}

export function PieSkeleton() {
  return (
    <div className="flex flex-col items-center gap-6">
      <Skeleton className="h-48 w-48 rounded-full" />
      <div className="grid w-full grid-cols-2 gap-x-6 gap-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-3 w-full" />
        ))}
      </div>
    </div>
  );
}

export function AlertsTableSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div>
      <div className="flex items-center justify-between border-b border-black/5 px-6 py-4">
        <div className="space-y-2">
          <Skeleton className="h-3 w-32" />
          <Skeleton className="h-2.5 w-48" />
        </div>
        <Skeleton className="h-3 w-16" />
      </div>
      <div className="flex items-center gap-4 border-b border-black/5 px-6 py-3">
        <Skeleton className="h-2.5 w-16" />
        <Skeleton className="h-2.5 w-40" />
        <Skeleton className="h-2.5 w-20" />
        <Skeleton className="h-2.5 w-20" />
        <Skeleton className="h-2.5 w-16" />
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-4 border-b border-black/5 px-6 py-4"
        >
          <Skeleton className="h-3 w-20" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-3 w-56" />
            <Skeleton className="h-2.5 w-32" />
          </div>
          <Skeleton className="h-5 w-20 rounded-full" />
          <Skeleton className="h-5 w-24 rounded-full" />
          <Skeleton className="h-3 w-16" />
        </div>
      ))}
    </div>
  );
}

export function AlertDetailsSkeleton() {
  return (
    <div className="flex h-full flex-col overflow-hidden rounded-3xl glass">
      <div className="flex items-center justify-between border-b border-black/5 px-6 py-4">
        <div className="space-y-2">
          <Skeleton className="h-2.5 w-20" />
          <Skeleton className="h-4 w-48" />
        </div>
        <Skeleton className="h-8 w-8 rounded-xl" />
      </div>
      <div className="flex-1 space-y-4 px-6 py-5">
        <div className="flex gap-2">
          <Skeleton className="h-5 w-20 rounded-full" />
          <Skeleton className="h-5 w-24 rounded-full" />
        </div>
        <div className="rounded-2xl border border-black/5 bg-black/[0.02] p-4 space-y-3">
          <div className="flex items-center justify-between">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-7 w-12" />
          </div>
          <Skeleton className="h-2 w-full rounded-full" />
        </div>
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="flex items-center gap-3 rounded-2xl border border-black/5 bg-black/[0.02] px-3.5 py-3"
          >
            <Skeleton className="h-9 w-9 rounded-xl" />
            <div className="flex-1 space-y-1.5">
              <Skeleton className="h-2 w-16" />
              <Skeleton className="h-3 w-32" />
            </div>
          </div>
        ))}
        <div className="space-y-2 pt-2">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-2/3" />
        </div>
      </div>
      <div className="flex gap-2.5 border-t border-black/5 p-5">
        <Skeleton className="h-10 flex-1 rounded-2xl" />
        <Skeleton className="h-10 flex-1 rounded-2xl" />
      </div>
    </div>
  );
}

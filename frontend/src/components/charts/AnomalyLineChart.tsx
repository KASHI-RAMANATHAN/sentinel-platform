import { useMemo, useState } from 'react';
import type { AnomalyPoint } from '@/types';

interface AnomalyLineChartProps {
  data: AnomalyPoint[];
}

export default function AnomalyLineChart({ data }: AnomalyLineChartProps) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const width = 760;
  const height = 260;
  const padding = { top: 24, right: 20, bottom: 36, left: 48 };
  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;

  const maxNormal = Math.max(0, ...data.map((d) => d.normal)) * 1.1;
  const maxAnomaly = Math.max(0, ...data.map((d) => d.anomalies)) * 1.3;

  const safeMaxNormal = maxNormal === 0 ? 1 : maxNormal;
  const safeMaxAnomaly = maxAnomaly === 0 ? 1 : maxAnomaly;

  const xFor = (i: number) =>
    data.length <= 1 ? padding.left : padding.left + (i / (data.length - 1)) * innerW;
  const yNormal = (v: number) =>
    padding.top + innerH - (v / safeMaxNormal) * innerH;
  const yAnomaly = (v: number) =>
    padding.top + innerH - (v / safeMaxAnomaly) * innerH;

  const normalPath = useMemo(() => {
    return data
      .map((d, i) => {
        const x = xFor(i);
        const y = yNormal(d.normal);
        if (i === 0) return `M ${x} ${y}`;
        const prev = data[i - 1];
        const px = xFor(i - 1);
        const py = yNormal(prev.normal);
        const cx = (px + x) / 2;
        return `C ${cx} ${py} ${cx} ${y} ${x} ${y}`;
      })
      .join(' ');
  }, [data]);

  const anomalyPath = useMemo(() => {
    return data
      .map((d, i) => {
        const x = xFor(i);
        const y = yAnomaly(d.anomalies);
        if (i === 0) return `M ${x} ${y}`;
        const prev = data[i - 1];
        const px = xFor(i - 1);
        const py = yAnomaly(prev.anomalies);
        const cx = (px + x) / 2;
        return `C ${cx} ${py} ${cx} ${y} ${x} ${y}`;
      })
      .join(' ');
  }, [data]);

  const anomalyArea = useMemo(() => {
    const base = `${anomalyPath} L ${xFor(data.length - 1)} ${padding.top + innerH} L ${xFor(0)} ${padding.top + innerH} Z`;
    return base;
  }, [anomalyPath, data.length]);

  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((t) => ({
    value: Math.round(maxAnomaly * t),
    y: padding.top + innerH - t * innerH,
  }));

  return (
    <div className="relative w-full">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-auto"
        onMouseLeave={() => setHoverIndex(null)}
      >
        <defs>
          <linearGradient id="anomalyArea" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="currentColor" className="text-black dark:text-white" stopOpacity="0.1" />
            <stop offset="100%" stopColor="currentColor" className="text-black dark:text-white" stopOpacity="0" />
          </linearGradient>
        </defs>

        {yTicks.map((t, i) => (
          <g key={i}>
            <line
              x1={padding.left}
              y1={t.y}
              x2={width - padding.right}
              y2={t.y}
              className="stroke-black/10 dark:stroke-white/10"
              strokeWidth="1"
              strokeDasharray="3 5"
            />
            <text
              x={padding.left - 10}
              y={t.y + 4}
              textAnchor="end"
              className="fill-black/40 dark:fill-white/40 font-mono"
              fontSize="10"
            >
              {t.value}
            </text>
          </g>
        ))}

        {data.map((d, i) => (
          <text
            key={i}
            x={xFor(i)}
            y={height - 12}
            textAnchor="middle"
            className="fill-black/40 dark:fill-white/40 font-mono"
            fontSize="10"
          >
            {d.time}
          </text>
        ))}

        <path d={anomalyArea} fill="url(#anomalyArea)" />
        <path
          d={normalPath}
          fill="none"
          className="stroke-black/20 dark:stroke-white/20"
          strokeWidth="2.5"
          strokeLinecap="square"
        />
        <path
          d={anomalyPath}
          fill="none"
          className="stroke-black dark:stroke-white"
          strokeWidth="2.5"
          strokeLinecap="square"
        />

        {data.map((d, i) => (
          <g key={i}>
            <rect
              x={xFor(i) - innerW / data.length / 2}
              y={padding.top}
              width={innerW / data.length}
              height={innerH}
              fill="transparent"
              onMouseEnter={() => setHoverIndex(i)}
            />
            {hoverIndex === i && (
              <line
                x1={xFor(i)}
                y1={padding.top}
                x2={xFor(i)}
                y2={padding.top + innerH}
                className="stroke-black/20 dark:stroke-white/20"
                strokeWidth="1"
                strokeDasharray="3 3"
              />
            )}
            <rect
              x={xFor(i) - (hoverIndex === i ? 4 : 2)}
              y={yAnomaly(d.anomalies) - (hoverIndex === i ? 4 : 2)}
              width={hoverIndex === i ? 8 : 4}
              height={hoverIndex === i ? 8 : 4}
              className="fill-white dark:fill-black stroke-black dark:stroke-white transition-all"
              strokeWidth="2"
            />
            <rect
              x={xFor(i) - (hoverIndex === i ? 4 : 2)}
              y={yNormal(d.normal) - (hoverIndex === i ? 4 : 2)}
              width={hoverIndex === i ? 8 : 4}
              height={hoverIndex === i ? 8 : 4}
              className="fill-white dark:fill-black stroke-black/40 dark:stroke-white/40 transition-all"
              strokeWidth="2"
            />
          </g>
        ))}

        {hoverIndex !== null && (
          <g>
            <rect
              x={Math.min(xFor(hoverIndex) + 12, width - 132)}
              y={padding.top + 8}
              width="120"
              height="56"
              className="fill-white dark:fill-black stroke-black/20 dark:stroke-white/20"
              strokeWidth="1"
            />
            <text
              x={Math.min(xFor(hoverIndex) + 22, width - 122)}
              y={padding.top + 26}
              className="fill-black/40 dark:fill-white/40 font-mono"
              fontSize="10"
            >
              {data[hoverIndex].time}
            </text>
            <rect
              x={Math.min(xFor(hoverIndex) + 16, width - 128)}
              y={padding.top + 39}
              width="4"
              height="4"
              className="fill-black dark:fill-white"
            />
            <text
              x={Math.min(xFor(hoverIndex) + 28, width - 116)}
              y={padding.top + 45}
              className="fill-black dark:fill-white font-mono"
              fontSize="10"
            >
              Anom: {data[hoverIndex].anomalies}
            </text>
            <rect
              x={Math.min(xFor(hoverIndex) + 16, width - 128)}
              y={padding.top + 53}
              width="4"
              height="4"
              className="fill-black/40 dark:fill-white/40"
            />
            <text
              x={Math.min(xFor(hoverIndex) + 28, width - 116)}
              y={padding.top + 59}
              className="fill-black/60 dark:fill-white/60 font-mono"
              fontSize="10"
            >
              Norm: {data[hoverIndex].normal}
            </text>
          </g>
        )}
      </svg>
    </div>
  );
}

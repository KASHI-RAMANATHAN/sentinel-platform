import { useState } from 'react';
import type { AttackType } from '@/types';

interface AttackPieChartProps {
  data: AttackType[];
}

export default function AttackPieChart({ data }: AttackPieChartProps) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const rawTotal = data.reduce((sum, d) => sum + d.value, 0);
  const total = rawTotal === 0 ? 1 : rawTotal;

  const size = 220;
  const center = size / 2;
  const radius = 84;
  const innerRadius = 54;
  const gap = 0.04;

  const segments = data.map((d, i) => {
    const startAngle =
      data.slice(0, i).reduce((s, x) => s + (x.value / total) * Math.PI * 2, 0) +
      gap / 2;
    const endAngle =
      startAngle + (d.value / total) * Math.PI * 2 - gap;
    const angleMid = (startAngle + endAngle) / 2;

    const x1 = center + radius * Math.cos(startAngle);
    const y1 = center + radius * Math.sin(startAngle);
    const x2 = center + radius * Math.cos(endAngle);
    const y2 = center + radius * Math.sin(endAngle);
    const x3 = center + innerRadius * Math.cos(endAngle);
    const y3 = center + innerRadius * Math.sin(endAngle);
    const x4 = center + innerRadius * Math.cos(startAngle);
    const y4 = center + innerRadius * Math.sin(startAngle);

    const largeArc = endAngle - startAngle > Math.PI ? 1 : 0;
    const path = `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} L ${x3} ${y3} A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${x4} ${y4} Z`;

    const expand = hoverIndex === i ? 6 : 0;
    const labelX = center + (radius + 14 + expand) * Math.cos(angleMid);
    const labelY = center + (radius + 14 + expand) * Math.sin(angleMid);

    return { path, color: d.color, labelX, labelY, expand, angleMid };
  });

  const hovered = hoverIndex !== null ? data[hoverIndex] : null;

  return (
    <div className="flex flex-col items-center gap-6">
      <div className="relative">
        <svg
          viewBox={`0 0 ${size} ${size}`}
          className="w-52 h-52"
          onMouseLeave={() => setHoverIndex(null)}
        >
          {segments.map((seg, i) => (
            <path
              key={i}
              d={seg.path}
              className={`transition-all duration-200 cursor-pointer ${seg.color}`}
              style={{ opacity: hoverIndex === null || hoverIndex === i ? 1 : 0.35 }}
              transform={`translate(${Math.cos(seg.angleMid) * seg.expand} ${Math.sin(seg.angleMid) * seg.expand})`}
              onMouseEnter={() => setHoverIndex(i)}
            />
          ))}
          <circle cx={center} cy={center} r={innerRadius - 4} className="fill-white dark:fill-black" />
          <circle cx={center} cy={center} r={innerRadius - 4} fill="none" className="stroke-black/10 dark:stroke-white/10" strokeWidth="1" />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-2xl font-bold text-black dark:text-white font-mono">
            {hovered ? `${hovered.value}%` : `${total}%`}
          </span>
          <span className="text-[10px] uppercase tracking-wider text-black/40 dark:text-white/40 mt-1">
            {hovered ? hovered.label : 'Total'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-x-6 gap-y-2 w-full">
        {data.map((d, i) => (
          <button
            key={d.label}
            className="flex items-center gap-2 text-left group"
            onMouseEnter={() => setHoverIndex(i)}
            onMouseLeave={() => setHoverIndex(null)}
          >
            <span
              className={`w-2.5 h-2.5 rounded-none shrink-0 transition-transform group-hover:scale-125 ${d.color.replace(/fill-/g, 'bg-')}`}
            />
            <span
              className={`text-[10px] uppercase tracking-wider transition-colors font-mono ${hoverIndex === i ? 'text-black dark:text-white' : 'text-black/60 dark:text-white/60'
                }`}
            >
              {d.label}
            </span>
            <span className="ml-auto text-[10px] font-mono text-black/40 dark:text-white/40">
              {d.value}%
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
interface StatusDotProps {
  color?: 'green' | 'red' | 'orange' | 'blue' | 'indigo';
  pulse?: boolean;
  className?: string;
}

const colorMap = {
  green: 'bg-black dark:bg-white',
  red: 'bg-black/60 dark:bg-white/60',
  orange: 'bg-black/40 dark:bg-white/40',
  blue: 'bg-black/20 dark:bg-white/20',
  indigo: 'bg-black/10 dark:bg-white/10',
};

const ringMap = {
  green: 'bg-black dark:bg-white',
  red: 'bg-black/60 dark:bg-white/60',
  orange: 'bg-black/40 dark:bg-white/40',
  blue: 'bg-black/20 dark:bg-white/20',
  indigo: 'bg-black/10 dark:bg-white/10',
};

export default function StatusDot({
  color = 'green',
  pulse = false,
  className = '',
}: StatusDotProps) {
  return (
    <span className={`relative flex h-2 w-2 ${className}`}>
      {pulse && (
        <span
          className={`absolute inline-flex h-full w-full animate-ping rounded-none ${ringMap[color]} opacity-60`}
        />
      )}
      <span
        className={`relative inline-flex h-2 w-2 rounded-none ${colorMap[color]}`}
      />
    </span>
  );
}

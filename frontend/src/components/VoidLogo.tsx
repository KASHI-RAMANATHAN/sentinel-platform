export default function VoidLogo({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M 0 50 C 35 50, 42 48, 48 42 C 48 42, 50 40, 50 40 C 50 40, 52 42, 52 42 C 58 48, 65 50, 100 50" stroke="currentColor" strokeWidth="2.5" />
      <path d="M 0 50 C 35 50, 42 52, 48 58 C 48 58, 50 60, 50 60 C 50 60, 52 58, 52 58 C 58 52, 65 50, 100 50" stroke="currentColor" strokeWidth="2.5" />
      
      <path d="M 15 50 A 35 35 0 1 1 85 50" stroke="currentColor" strokeWidth="2.5" />
      <path d="M 15 50 A 35 35 0 1 0 85 50" stroke="currentColor" strokeWidth="2.5" />
    </svg>
  );
}

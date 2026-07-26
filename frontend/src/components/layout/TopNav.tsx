import { useState, useEffect } from 'react';
import { Menu, Search, Bell, ChevronDown, Terminal, Moon, Sun } from 'lucide-react';

interface TopNavProps {
  onMenuClick: () => void;
  isDarkMode: boolean;
  onToggleDarkMode: () => void;
}

export default function TopNav({ onMenuClick, isDarkMode, onToggleDarkMode }: TopNavProps) {
  const [time, setTime] = useState('');

  useEffect(() => {
    const updateTime = () => setTime(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', timeZoneName: 'short' }));
    updateTime();
    const interval = setInterval(updateTime, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-20 px-4 pt-4 lg:px-8">
      <div className="flex h-14 items-center gap-3 rounded-none border border-black/20 bg-white px-4 dark:border-white/20 dark:bg-black">
        <button
          onClick={onMenuClick}
          className="flex h-9 w-9 items-center justify-center rounded-none text-black transition-colors hover:bg-black/5 dark:text-white dark:hover:bg-white/10 lg:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Search */}
        <div className="relative hidden flex-1 sm:block sm:max-w-md">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-black/40 dark:text-white/40" />
          <input
            type="text"
            placeholder="Search alerts, IPs, devices..."
            className="w-full rounded-none border border-black/20 bg-transparent py-2 pl-9 pr-16 text-sm text-black placeholder:text-black/40 outline-none transition-colors focus:border-black dark:border-white/20 dark:text-white dark:placeholder:text-white/40 dark:focus:border-white"
          />
          <kbd className="pointer-events-none absolute right-2.5 top-1/2 hidden -translate-y-1/2 rounded-none border border-black/20 bg-transparent px-1.5 py-0.5 font-mono text-[10px] text-black/60 dark:border-white/20 dark:text-white/60 md:block">
            ⌘K
          </kbd>
        </div>

        <div className="ml-auto flex items-center gap-2">
          {/* Clock */}
          <div className="hidden items-center gap-2 rounded-none border border-black/20 bg-transparent px-3 py-1.5 dark:border-white/20 md:flex">
            <Terminal className="h-3.5 w-3.5 text-black dark:text-white" />
            <span className="font-mono text-xs text-black dark:text-white">{time}</span>
          </div>

          {/* Theme Toggle */}
          <button 
            onClick={onToggleDarkMode}
            className="flex h-9 w-9 items-center justify-center rounded-none text-black transition-colors hover:bg-black/5 dark:text-white dark:hover:bg-white/10"
          >
            {isDarkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </button>

          <div className="mx-1 h-6 w-px bg-black/20 dark:bg-white/20" />

          {/* Profile */}
          <button className="flex items-center gap-2 rounded-none py-1.5 pl-1.5 pr-2 transition-colors hover:bg-black/5 dark:hover:bg-white/10">
            <div className="flex h-7 w-7 items-center justify-center rounded-none border border-black bg-black text-xs font-semibold text-white dark:border-white dark:bg-white dark:text-black">
              KV
            </div>
            <div className="hidden text-left sm:block">
              <p className="text-xs font-medium leading-none text-black dark:text-white">
                Kashi Valliappa
              </p>
              <p className="mt-1 text-[10px] text-black/60 dark:text-white/60">Analyst</p>
            </div>
            <ChevronDown className="hidden h-4 w-4 text-black/40 dark:text-white/40 sm:block" />
          </button>
        </div>
      </div>
    </header>
  );
}

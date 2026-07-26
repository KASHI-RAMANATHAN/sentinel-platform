import {
  LayoutDashboard,
  ShieldAlert,
  Server,
  Network,
  FileBarChart,
  SlidersHorizontal,
  ScrollText,
  Settings,
  LifeBuoy,
  X,
  Cpu,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { NavItem } from '@/types';
import StatusDot from '@/components/dashboard/StatusDot';
import VoidLogo from '@/components/VoidLogo';

export const navItems: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: 'LayoutDashboard' },
  { id: 'alerts', label: 'Alerts', icon: 'ShieldAlert' },
  { id: 'devices', label: 'Devices', icon: 'Server' },
  { id: 'network', label: 'Network', icon: 'Network' },
  { id: 'reports', label: 'Reports', icon: 'FileBarChart' },
  { id: 'rules', label: 'Detection Rules', icon: 'SlidersHorizontal' },
  { id: 'audit', label: 'Audit Log', icon: 'ScrollText' },
];

export const secondaryNav: NavItem[] = [
  { id: 'about', label: 'About Project', icon: 'LifeBuoy' },
];

interface SidebarProps {
  activeId: string;
  onSelect: (id: string) => void;
  mobileOpen: boolean;
  onClose: () => void;
  alertsCount?: number;
}

const iconMap: Record<string, LucideIcon> = {
  LayoutDashboard,
  ShieldAlert,
  Server,
  Network,
  FileBarChart,
  SlidersHorizontal,
  ScrollText,
  Settings,
  LifeBuoy,
};

function NavButton({
  item,
  active,
  onClick,
}: {
  item: NavItem;
  active: boolean;
  onClick: () => void;
}) {
  const Icon = iconMap[item.icon] ?? LayoutDashboard;
  return (
    <button
      onClick={onClick}
      className={`group relative flex w-full items-center gap-3 rounded-none border px-3.5 py-2.5 text-sm transition-all duration-200 ${
        active
          ? 'border-black bg-black text-white dark:border-white dark:bg-white dark:text-black'
          : 'border-transparent text-black/60 hover:border-black/20 hover:bg-black/5 hover:text-black dark:text-white/60 dark:hover:border-white/20 dark:hover:bg-white/10 dark:hover:text-white'
      }`}
    >
      <Icon
        className={`h-[18px] w-[18px] shrink-0 transition-colors ${
          active ? 'text-white dark:text-black' : 'text-black/40 group-hover:text-black/70 dark:text-white/40 dark:group-hover:text-white/70'
        }`}
        strokeWidth={1.5}
      />
      <span className="flex-1 text-left">{item.label}</span>
      {item.badge && (
        <span className="rounded-none border border-black bg-transparent px-2 py-0.5 text-[10px] font-mono font-semibold text-black dark:border-white dark:text-white">
          {item.badge}
        </span>
      )}
    </button>
  );
}

export default function Sidebar({
  activeId,
  onSelect,
  mobileOpen,
  onClose,
  alertsCount = 0,
}: SidebarProps) {
  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 backdrop-blur-sm lg:hidden dark:bg-black/80"
          onClick={onClose}
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col bg-white border-r border-black/20 transition-transform duration-300 dark:bg-black dark:border-white/20 lg:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-full flex-col overflow-hidden">
          {/* Brand */}
          <div className="flex items-center justify-between px-5 py-5 border-b border-black/10 dark:border-white/10">
            <div className="flex items-center gap-3">
              <div className="relative flex h-10 w-10 items-center justify-center">
                <VoidLogo className="h-8 w-8 text-black dark:text-white" />
              </div>
              <div>
                <p className="text-[15px] font-semibold leading-none text-black dark:text-white">
                  Sentinel
                </p>
                <p className="mt-1 font-mono text-[10px] uppercase tracking-wider text-black/60 dark:text-white/60">
                  Security Console
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-none text-black/40 transition-colors hover:bg-black/5 dark:text-white/40 dark:hover:bg-white/10 lg:hidden"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Nav */}
          <nav className="flex-1 overflow-y-auto px-3 py-2">
            <p className="px-3.5 pb-2 pt-3 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Monitoring
            </p>
            <div className="space-y-1">
              {navItems.map((item) => (
                <NavButton
                  key={item.id}
                  item={{ ...item, badge: item.id === 'alerts' && alertsCount > 0 ? String(alertsCount) : undefined }}
                  active={activeId === item.id}
                  onClick={() => {
                    onSelect(item.id);
                    onClose();
                  }}
                />
              ))}
            </div>

            <p className="px-3.5 pb-2 pt-6 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              System
            </p>
            <div className="space-y-1">
              {secondaryNav.map((item) => (
                <NavButton
                  key={item.id}
                  item={item}
                  active={activeId === item.id}
                  onClick={() => {
                    onSelect(item.id);
                    onClose();
                  }}
                />
              ))}
            </div>
          </nav>

          {/* Status footer */}
          <div className="mt-auto border-t border-black/10 p-5 dark:border-white/10">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 bg-black dark:bg-white animate-pulse" />
                <span className="font-mono text-[10px] text-black/60 dark:text-white/60 uppercase tracking-wider">
                  Sys Status
                </span>
              </div>
              <span className="font-mono text-[10px] text-black dark:text-white uppercase tracking-wider">
                Active
              </span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

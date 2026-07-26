import type {
  Alert,
  AnomalyPoint,
  AttackType,
  Kpi,
  NavItem,
} from '@/types';

export const kpis: Kpi[] = [
  {
    label: 'Total Sessions',
    value: '24,892',
    delta: '+12.4%',
    trend: 'up',
    positive: true,
    icon: 'sessions',
  },
  {
    label: 'Active Threats',
    value: '37',
    delta: '+5',
    trend: 'up',
    positive: false,
    icon: 'threats',
  },
  {
    label: 'Average Risk Score',
    value: '42.7',
    delta: '-3.2%',
    trend: 'down',
    positive: true,
    icon: 'risk',
  },
  {
    label: 'Devices Monitored',
    value: '1,284',
    delta: '+18',
    trend: 'up',
    positive: true,
    icon: 'devices',
  },
];

export const anomalyTrend: AnomalyPoint[] = [
  { time: '00:00', anomalies: 12, normal: 820 },
  { time: '03:00', anomalies: 8, normal: 760 },
  { time: '06:00', anomalies: 15, normal: 910 },
  { time: '09:00', anomalies: 34, normal: 1240 },
  { time: '12:00', anomalies: 41, normal: 1480 },
  { time: '15:00', anomalies: 28, normal: 1320 },
  { time: '18:00', anomalies: 52, normal: 1620 },
  { time: '21:00', anomalies: 19, normal: 980 },
];

export const attackDistribution: AttackType[] = [
  { label: 'Malware', value: 38, color: '#FF3B30' },
  { label: 'Phishing', value: 24, color: '#FF9500' },
  { label: 'DDoS', value: 18, color: '#007AFF' },
  { label: 'Brute Force', value: 12, color: '#5856D6' },
  { label: 'Insider', value: 8, color: '#34C759' },
];

export const alerts: Alert[] = [
  {
    id: 'ALT-4821',
    title: 'Suspicious login from new geo-location',
    severity: 'critical',
    status: 'investigating',
    source: '203.0.113.45',
    destination: 'auth-service-01',
    category: 'Credential Abuse',
    timestamp: '2 min ago',
    riskScore: 92,
    description:
      'Multiple failed authentication attempts followed by a successful login from an IP address in an unapproved region. User account "j.mercer" was accessed at 14:32 UTC after 7 failed attempts.',
    protocol: 'HTTPS',
    port: 443,
  },
  {
    id: 'ALT-4820',
    title: 'Unusual outbound data transfer detected',
    severity: 'high',
    status: 'open',
    source: '10.14.22.8',
    destination: '198.51.100.12',
    category: 'Data Exfiltration',
    timestamp: '11 min ago',
    riskScore: 81,
    description:
      'Endpoint FIN-WS-014 transferred 2.3 GB to an external host over an encrypted channel outside of scheduled backup windows. Destination IP is not on the approved vendor list.',
    protocol: 'TLS',
    port: 8443,
  },
  {
    id: 'ALT-4819',
    title: 'Port scan detected on edge firewall',
    severity: 'medium',
    status: 'blocked',
    source: '45.33.21.88',
    destination: 'firewall-edge-01',
    category: 'Reconnaissance',
    timestamp: '24 min ago',
    riskScore: 54,
    description:
      'Sequential TCP SYN probes across ports 1-1024 were detected and automatically dropped by the edge firewall. Source IP has been added to the temporary block list for 24 hours.',
    protocol: 'TCP',
    port: 1024,
  },
  {
    id: 'ALT-4818',
    title: 'Malware signature matched on endpoint',
    severity: 'critical',
    status: 'investigating',
    source: '10.14.22.31',
    destination: 'localhost',
    category: 'Malware',
    timestamp: '38 min ago',
    riskScore: 88,
    description:
      'EDR agent on endpoint HR-WS-042 matched signature TRJ/WannaCrypt.gen against a process spawning from a macro-enabled document. Process tree has been frozen for analysis.',
    protocol: 'SMB',
    port: 445,
  },
  {
    id: 'ALT-4817',
    title: 'Privileged account created outside change window',
    severity: 'high',
    status: 'open',
    source: '10.14.22.5',
    destination: 'dc-internal-02',
    category: 'Privilege Misuse',
    timestamp: '52 min ago',
    riskScore: 76,
    description:
      'A new domain admin account "svc_deploy" was created on dc-internal-02 outside of the approved change window. No corresponding change ticket was found in the ITSM system.',
    protocol: 'LDAP',
    port: 389,
  },
  {
    id: 'ALT-4816',
    title: 'Repeated failed VPN authentications',
    severity: 'medium',
    status: 'blocked',
    source: '192.0.2.77',
    destination: 'vpn-gateway-01',
    category: 'Brute Force',
    timestamp: '1 hr ago',
    riskScore: 61,
    description:
      '142 failed VPN login attempts were observed over 4 minutes targeting the "admin" account. The source IP was rate-limited and blocked after threshold was exceeded.',
    protocol: 'UDP',
    port: 500,
  },
  {
    id: 'ALT-4815',
    title: 'Phishing URL clicked in client email',
    severity: 'low',
    status: 'resolved',
    source: 'mail-gateway-01',
    destination: '10.14.22.41',
    category: 'Phishing',
    timestamp: '2 hr ago',
    riskScore: 34,
    description:
      'A filtered phishing message reached a user inbox and a link was clicked. URL was sandboxed and did not resolve to a live payload. User has been enrolled in refresher training.',
    protocol: 'SMTP',
    port: 25,
  },
  {
    id: 'ALT-4814',
    title: 'Unauthorized USB device connected',
    severity: 'low',
    status: 'resolved',
    source: '10.14.22.19',
    destination: 'localhost',
    category: 'Policy Violation',
    timestamp: '3 hr ago',
    riskScore: 29,
    description:
      'A USB mass storage device was connected to endpoint ENG-WS-008 in violation of DLP policy. Device was automatically unmounted and the event was logged for review.',
    protocol: 'USB',
    port: 0,
  },
];

export const navItems: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: 'LayoutDashboard' },
  { id: 'alerts', label: 'Alerts', icon: 'ShieldAlert', badge: '37' },
  { id: 'devices', label: 'Devices', icon: 'Server' },
  { id: 'network', label: 'Network', icon: 'Network' },
  { id: 'reports', label: 'Reports', icon: 'FileBarChart' },
  { id: 'rules', label: 'Detection Rules', icon: 'SlidersHorizontal' },
  { id: 'audit', label: 'Audit Log', icon: 'ScrollText' },
];

export const secondaryNav: NavItem[] = [
  { id: 'settings', label: 'Settings', icon: 'Settings' },
  { id: 'help', label: 'Help Center', icon: 'LifeBuoy' },
];

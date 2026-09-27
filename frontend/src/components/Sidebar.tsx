import React from 'react';
import { Mic, FolderOpen, CheckSquare, Settings, ShieldCheck, Sparkles } from 'lucide-react';

export type TabType = 'studio' | 'meetings' | 'actions' | 'settings';

interface Props {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  meetingCount: number;
}

export const Sidebar: React.FC<Props> = ({ activeTab, onTabChange, meetingCount }) => {
  const navItems: { id: TabType; label: string; icon: React.ReactNode; badge?: number }[] = [
    { id: 'studio', label: 'Live Studio', icon: <Mic size={18} /> },
    { id: 'meetings', label: 'All Sessions', icon: <FolderOpen size={18} />, badge: meetingCount },
    { id: 'actions', label: 'Action Items', icon: <CheckSquare size={18} /> },
    { id: 'settings', label: 'AI & Settings', icon: <Settings size={18} /> },
  ];

  return (
    <aside className="sidebar">
      {/* Brand Logo Header */}
      <div className="sidebar-brand">
        <div className="brand-icon">
          <Sparkles size={20} color="#00F2FE" />
        </div>
        <div className="brand-text">
          <span className="brand-name">SonoScribe</span>
          <span className="brand-tagline">AI Meeting Suite</span>
        </div>
      </div>

      {/* Navigation List */}
      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => onTabChange(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="nav-badge">{item.badge}</span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer Security Badge */}
      <div className="sidebar-footer">
        <div className="privacy-badge">
          <ShieldCheck size={14} color="var(--accent-green)" />
          <span>Local Engine Active</span>
        </div>
      </div>
    </aside>
  );
};

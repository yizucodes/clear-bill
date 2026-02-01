'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import { Sparkles, FileText, Search } from 'lucide-react';

export default function Navigation() {
  const pathname = usePathname();

  const tabs = [
    { href: '/', label: 'Advisor', icon: Search, description: 'Find care' },
    { href: '/dispute', label: 'Dispute', icon: FileText, description: 'Fight bills' },
  ];

  return (
    <nav className="nav-container">
      <div className="nav-inner">
        {/* Logo */}
        <Link href="/" className="nav-logo">
          <Sparkles size={24} className="icon-primary" />
          <span className="nav-logo-text">ClearBill</span>
        </Link>

        {/* Tabs */}
        <div className="nav-tabs">
          {tabs.map((tab) => {
            const isActive = pathname === tab.href;
            const Icon = tab.icon;

            return (
              <Link
                key={tab.href}
                href={tab.href}
                className={`nav-tab ${isActive ? 'active' : ''}`}
              >
                <Icon size={18} />
                <span>{tab.label}</span>
                {isActive && (
                  <motion.div
                    layoutId="activeTab"
                    className="nav-tab-indicator"
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  />
                )}
              </Link>
            );
          })}
        </div>

        {/* Spacer */}
        <div className="nav-spacer" />
      </div>
    </nav>
  );
}

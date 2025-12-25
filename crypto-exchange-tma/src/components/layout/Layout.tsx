import React from 'react';
import { Header } from './Header';
import { Navigation } from './Navigation';
import './Layout.css';

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  showNavigation?: boolean;
}

export function Layout({ 
  children, 
  title, 
  subtitle,
  showNavigation = true 
}: LayoutProps) {
  return (
    <div className="layout">
      <Header title={title} subtitle={subtitle} />
      <main className={`layout-content ${showNavigation ? 'with-nav' : ''}`}>
        {children}
      </main>
      {showNavigation && <Navigation />}
    </div>
  );
}

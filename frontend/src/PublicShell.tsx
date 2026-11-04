import type { ReactNode } from 'react';
import { Icon } from './Icon';
import { PRODUCT_VERSION } from './version';
import './styles.css';
import './public.css';

export function PublicShell({ page, mainId, children }: { page: 'overview' | 'prepare' | 'grid'; mainId: string; children: ReactNode }) {
  return <div className="public-product">
    <a className="skip-link" href={'#' + mainId}>Skip to content</a>
    <header className="site-header no-print"><div className="header-inner">
      <a className="brand" href="/" title="GridGuide overview"><span className="brand-mark"><Icon name="network"/></span><span><strong>GridGuide</strong>{' '}<small>AI Outage Concierge</small></span></a>
      <nav className="product-nav" aria-label="Main navigation">
        <a href="/" aria-current={page === 'overview' ? 'page' : undefined}>Overview</a>
        <a href="/preparedness/" aria-current={page === 'prepare' ? 'page' : undefined}>Prepare & alerts</a>
        <a href="/operator/" aria-current={page === 'grid' ? 'page' : undefined}>Grid insights</a>
      </nav>
      <span className="prototype-identity">Portfolio demo<br/>Fictional scenarios</span>
    </div></header>
    {children}
    <footer className="site-footer no-print"><p>GridGuide {PRODUCT_VERSION} portfolio release<br/><strong>Fictional demonstration · no live utility connection</strong></p><p>Python-owned results. Standard explanations.<br/>No dispatch, subscriptions or alert delivery.</p></footer>
  </div>;
}

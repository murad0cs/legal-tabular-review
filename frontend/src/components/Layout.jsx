import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, FileText, Layers, FolderKanban, Search } from 'lucide-react';
import clsx from 'clsx';
import ThemeToggle from './ThemeToggle.jsx';
import GlobalSearch from './GlobalSearch.jsx';

const NAV_ITEMS = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/documents', icon: FileText, label: 'Documents' },
  { path: '/templates', icon: Layers, label: 'Templates' },
  { path: '/projects', icon: FolderKanban, label: 'Projects' },
];

function Layout({ children }) {
  const location = useLocation();
  const [searchOpen, setSearchOpen] = useState(false);

  // Keyboard shortcut for search (Ctrl+K or Cmd+K)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen(true);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex transition-colors">
      <aside className="w-64 bg-white dark:bg-slate-800/50 border-r border-slate-200 dark:border-slate-700 flex flex-col transition-colors">
        <div className="p-6 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary-500/20 flex items-center justify-center">
              <Layers className="w-6 h-6 text-primary-400" />
            </div>
            <div>
              <h1 className="font-bold text-slate-900 dark:text-white">Legal Review</h1>
              <p className="text-xs text-slate-500">Tabular Extraction</p>
            </div>
          </Link>
          <ThemeToggle />
        </div>

        {/* Search Button */}
        <div className="px-4 mb-4">
          <button
            onClick={() => setSearchOpen(true)}
            className="w-full flex items-center gap-3 px-4 py-2.5 bg-slate-100 dark:bg-slate-800/50 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-xl text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-white transition-colors"
          >
            <Search className="w-4 h-4" />
            <span className="text-sm">Search...</span>
            <kbd className="ml-auto text-xs bg-slate-200 dark:bg-slate-700 px-1.5 py-0.5 rounded">⌘K</kbd>
          </button>
        </div>

        <nav className="flex-1 px-4">
          <ul className="space-y-1">
            {NAV_ITEMS.map(({ path, icon: Icon, label }) => {
              const isActive = location.pathname === path || (path !== '/' && location.pathname.startsWith(path));
              return (
                <li key={path}>
                    <Link
                      to={path}
                      className={clsx(
                        'flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200',
                        isActive 
                          ? 'bg-primary-500/20 text-primary-500' 
                          : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/50'
                      )}
                    >
                    <Icon className="w-5 h-5" />
                    <span className="font-medium">{label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="p-4 text-center text-xs text-slate-400 dark:text-slate-600">
          v1.0.0 • Legal Tabular Review
        </div>
      </aside>

      <main className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto p-8">{children}</div>
      </main>

      {/* Global Search Modal */}
      <GlobalSearch isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </div>
  );
}

export default Layout;

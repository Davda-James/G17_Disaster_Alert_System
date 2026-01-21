import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield, 
  User, 
  MapPin, 
  History, 
  Settings, 
  LogOut, 
  ChevronLeft, 
  ChevronRight,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import SettingsModal from './SettingsModal'; // <--- Import the new component

interface DashboardSidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
}

export default function DashboardSidebar({ isCollapsed, onToggle }: DashboardSidebarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  // New State for controlling the modal
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const menuItems = [
    { icon: MapPin, label: 'Dashboard', path: '/dashboard' },
    { icon: History, label: 'Alert History', path: '/dashboard/alerts' },
    // Removed Profile path to keep it simple, or you can map it to settings too
    { icon: Settings, label: 'Settings', path: '#' }, 
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <>
      <motion.aside
        initial={false}
        animate={{ width: isCollapsed ? 80 : 280 }}
        className="relative h-screen glass-strong border-r border-border/50 flex flex-col z-20"
      >
        {/* Toggle Button */}
        <button
          onClick={onToggle}
          className="absolute -right-3 top-8 p-1.5 rounded-full bg-secondary border border-border hover:bg-accent transition-colors z-10"
        >
          {isCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>

        {/* Logo */}
        <div className="p-6 border-b border-border/50">
          <Link to="/dashboard" className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-primary/20 border border-primary/30 shrink-0">
              <Shield className="w-5 h-5 text-primary" />
            </div>
            <AnimatePresence>
              {!isCollapsed && (
                <motion.span
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: 'auto' }}
                  exit={{ opacity: 0, width: 0 }}
                  className="text-lg font-bold whitespace-nowrap overflow-hidden"
                >
                  DisasterWatch
                </motion.span>
              )}
            </AnimatePresence>
          </Link>
        </div>

        {/* User Profile */}
        <div className="p-4 border-b border-border/50">
          <div className="flex items-center gap-3">
            <Avatar className="w-10 h-10 shrink-0">
              <AvatarImage src={user?.avatar} />
              <AvatarFallback className="bg-primary/20 text-primary">
                {user?.name?.charAt(0) || 'U'}
              </AvatarFallback>
            </Avatar>
            <AnimatePresence>
              {!isCollapsed && (
                <motion.div
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: 'auto' }}
                  exit={{ opacity: 0, width: 0 }}
                  className="overflow-hidden"
                >
                  <p className="font-medium text-sm truncate">{user?.name || 'User'}</p>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    {user?.isAuthorized ? (
                      <>
                        <CheckCircle className="w-3 h-3 text-green-400" />
                        <span className="text-green-400">Authorized</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-3 h-3" />
                        <span>Standard User</span>
                      </>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {menuItems.map((item) => {
            // Logic to handle Settings differently
            if (item.label === 'Settings') {
              return (
                <button
                  key={item.label}
                  onClick={() => setIsSettingsOpen(true)}
                  className={`w-full flex items-center gap-3 px-3 py-3 rounded-lg transition-all text-muted-foreground hover:bg-secondary hover:text-foreground`}
                >
                  <item.icon className="w-5 h-5 shrink-0" />
                  <AnimatePresence>
                    {!isCollapsed && (
                      <motion.span
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="whitespace-nowrap"
                      >
                        {item.label}
                      </motion.span>
                    )}
                  </AnimatePresence>
                </button>
              );
            }

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-3 rounded-lg transition-all ${
                  isActive(item.path)
                    ? 'bg-primary/20 text-primary border border-primary/30'
                    : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                }`}
              >
                <item.icon className="w-5 h-5 shrink-0" />
                <AnimatePresence>
                  {!isCollapsed && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="whitespace-nowrap"
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>
              </Link>
            );
          })}
        </nav>

        {/* Logout */}
        <div className="p-4 border-t border-border/50">
          <Button
            variant="ghost"
            onClick={handleLogout}
            className={`w-full justify-start gap-3 text-muted-foreground hover:text-destructive hover:bg-destructive/10 ${
              isCollapsed ? 'px-3' : ''
            }`}
          >
            <LogOut className="w-5 h-5 shrink-0" />
            <AnimatePresence>
              {!isCollapsed && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  Logout
                </motion.span>
              )}
            </AnimatePresence>
          </Button>
        </div>
      </motion.aside>

      {/* RENDER THE SETTINGS MODAL HERE */}
      <SettingsModal 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
      />
    </>
  );
}
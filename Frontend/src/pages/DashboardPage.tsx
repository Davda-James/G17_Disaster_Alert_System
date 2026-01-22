import { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { Bell, Filter, Clock, Loader2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import DashboardSidebar from '@/components/DashboardSidebar';
import AlertsPanel from '@/components/AlertsPanel';
import NotifyAlertModal from '@/components/NotifyAlertModal';
import GlobeBackground from '@/components/GlobeBackground';
import { Button } from '@/components/ui/button';
import { SeverityBadge } from '@/components/SeverityBadge';
import { useToast } from "@/hooks/use-toast";
import { Alert } from '@/components/Alert'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

// Define the Alert Interface matching the Backend


export default function DashboardPage() {
  const { isAuthenticated, user } = useAuth();
  const { toast } = useToast();
  
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showNotifyModal, setShowNotifyModal] = useState(false);
  
  // State for Filters and Data
  const [timeFilter, setTimeFilter] = useState('30d');
  const [typeFilter, setTypeFilter] = useState('all');
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // --- 1. Fetch Alerts from Backend ---
  const fetchAlerts = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      // Build Query String
      const params = new URLSearchParams({
        time: timeFilter,
        type: typeFilter
      });

      const response = await fetch(`http://localhost:5000/api/alerts?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setAlerts(data);
      }
    } catch (error) {
      console.error("Failed to fetch alerts", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Run fetch whenever filters change
  useEffect(() => {
    fetchAlerts();
  }, [timeFilter, typeFilter]);

  // --- 2. Handle New Alert Creation ---
  const handleAlertCreated = async () => {
    // Refresh list and close modal
    await fetchAlerts();
    setShowNotifyModal(false);
    toast({
      title: "Alert Broadcasted",
      description: "Your alert has been saved to the global database.",
    });
  };

  const activeDisasters = alerts.filter(d => d.status === 'active' || !d.status).length;

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <DashboardSidebar 
        isCollapsed={sidebarCollapsed} 
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} 
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 border-b border-border/50 glass-strong flex items-center justify-between px-6 shrink-0 z-10">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-semibold">Global Disaster Monitor</h1>
            <span className="px-2 py-1 rounded-full bg-destructive/20 text-destructive text-xs font-medium">
              {activeDisasters} Active
            </span>
          </div>

          <div className="flex items-center gap-3">
            {/* Filters */}
            <Select value={timeFilter} onValueChange={setTimeFilter}>
              <SelectTrigger className="w-32 h-9 bg-secondary text-sm">
                <Clock className="w-3 h-3 mr-1" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="24h">Last 24h</SelectItem>
                <SelectItem value="7d">Last 7 days</SelectItem>
                <SelectItem value="30d">Last 30 days</SelectItem>
              </SelectContent>
            </Select>

            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-32 h-9 bg-secondary text-sm">
                <Filter className="w-3 h-3 mr-1" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="earthquake">Earthquake</SelectItem>
                <SelectItem value="flood">Flood</SelectItem>
                <SelectItem value="fire">Wildfire</SelectItem>
                <SelectItem value="cyclone">Cyclone</SelectItem>
                <SelectItem value="tsunami">Tsunami</SelectItem>
                <SelectItem value="landslide">Landslide</SelectItem>
                <SelectItem value="volcano">Volcanic Activity</SelectItem>
              </SelectContent>
            </Select>

            {/* Notify Button */}
            <Button 
              onClick={() => setShowNotifyModal(true)}
              className="glow-primary"
            >
              <Bell className="w-4 h-4 mr-2" />
              Notify Alert
            </Button>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 flex overflow-hidden">
          {/* Globe View */}
          <div className="flex-1 relative globe-container">
            <GlobeBackground interactive={true} showMarkers={true} alerts={alerts} />
            
            {/* Legend */}
            <div className="absolute bottom-6 left-6 glass rounded-lg p-4 z-10">
              <p className="text-xs text-muted-foreground mb-3 font-medium">Severity Legend</p>
              <div className="space-y-2">
                <SeverityBadge severity="critical">Critical</SeverityBadge>
                <SeverityBadge severity="high">High</SeverityBadge>
                <SeverityBadge severity="medium">Medium</SeverityBadge>
                <SeverityBadge severity="low">Low</SeverityBadge>
              </div>
            </div>

            {/* User Location Indicator */}
            <div className="absolute top-6 left-6 glass rounded-lg p-3 z-10">
              <p className="text-xs text-muted-foreground mb-1">Your Location</p>
              <p className="text-sm font-medium">{user?.location?.city || "Unknown"}, {user?.location?.state || ""}</p>
            </div>
          </div>

          {/* Alerts Panel */}
          <div className="w-80 border-l border-border/50 glass-strong shrink-0 flex flex-col">
            {isLoading ? (
              <div className="flex-1 flex items-center justify-center">
                <Loader2 className="w-6 h-6 animate-spin text-primary" />
              </div>
            ) : (
              <AlertsPanel alerts={alerts} />
            )}
          </div>
        </div>
      </div>

      {/* Notify Alert Modal */}
      <NotifyAlertModal 
        isOpen={showNotifyModal} 
        onClose={() => setShowNotifyModal(false)}
        onSuccess={handleAlertCreated} 
      />
    </div>
  );
}
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, Clock, MapPin, ChevronRight, AlertTriangle } from 'lucide-react';
import { SeverityBadge } from '@/components/SeverityBadge';
import { formatDistanceToNow } from 'date-fns';
import { Alert } from '@/components/Alert'; // <--- Updated Import

interface AlertsPanelProps {
  alerts: Alert[];
  onAlertClick?: (alert: Alert) => void;
}

export default function AlertsPanel({ alerts = [], onAlertClick }: AlertsPanelProps) {
  const [expandedAlert, setExpandedAlert] = useState<string | null>(null);

  // SAFE GUARD: Ensure alerts is always an array
  const safeAlerts = Array.isArray(alerts) ? alerts : [];

  // Sort Logic with Safety Check
  const sortedAlerts = [...safeAlerts].sort((a, b) => {
    const dateA = new Date(a.timestamp || Date.now());
    const dateB = new Date(b.timestamp || Date.now());
    return dateB.getTime() - dateA.getTime();
  });

  const handleAlertClick = (alert: Alert) => {
    setExpandedAlert(expandedAlert === alert.id ? null : alert.id);
    if (onAlertClick) onAlertClick(alert);
  };

  // Helper function to prevent Crash
  const getRelativeTime = (dateString: string) => {
    try {
      if (!dateString) return 'Just now';
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch (error) {
      return 'Just now'; // Fallback if date format is wrong
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-border/50 shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-primary" />
            <h2 className="font-semibold">Alert History</h2>
          </div>
          <span className="text-xs text-muted-foreground bg-secondary px-2 py-1 rounded-full">
            {safeAlerts.length} alerts
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin p-2 space-y-2">
        {sortedAlerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <AlertTriangle className="w-12 h-12 mb-4 opacity-50" />
            <p className="text-sm">No alerts found</p>
          </div>
        ) : (
          sortedAlerts.map((alert) => (
            <motion.div
              key={alert.id}
              initial={alert.isNew ? { scale: 1.02 } : false}
              animate={{ scale: 1 }}
              className={`relative rounded-lg border transition-all cursor-pointer ${
                alert.severity === 'critical' 
                  ? 'border-destructive/30 bg-destructive/5' 
                  : 'border-border/50 bg-card/50 hover:bg-card'
              }`}
              onClick={() => handleAlertClick(alert)}
            >
              <div className="p-3">
                <div className="flex items-start gap-3">
                  <SeverityBadge severity={alert.severity} size="sm" showDot={true}>
                    {alert.severity ? alert.severity.charAt(0).toUpperCase() : 'M'}
                  </SeverityBadge>
                  
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-sm truncate pr-4">{alert.title}</h3>
                    
                    <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                      <MapPin className="w-3 h-3 shrink-0" />
                      <span className="truncate">{alert.location}</span>
                    </div>
                    
                    <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                      <Clock className="w-3 h-3 shrink-0" />
                      {/* USE THE SAFE HELPER HERE */}
                      <span>{getRelativeTime(alert.timestamp)}</span>
                    </div>
                  </div>

                  <ChevronRight 
                    className={`w-4 h-4 text-muted-foreground transition-transform shrink-0 ${
                      expandedAlert === alert.id ? 'rotate-90' : ''
                    }`} 
                  />
                </div>

                <AnimatePresence>
                  {expandedAlert === alert.id && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <p className="mt-3 pt-3 border-t border-border/50 text-sm text-muted-foreground">
                        {alert.message}
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}
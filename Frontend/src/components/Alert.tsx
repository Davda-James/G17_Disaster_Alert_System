export interface Alert {
  id: string;
  title: string;
  message: string;
  type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  location: string;
  coordinates?: {
    lat: number;
    lng: number;
  };
  timestamp: string;
  status?: string;
  isNew?: boolean;
}
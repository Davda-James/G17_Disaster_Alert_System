export interface Disaster {
  id: string;
  type: 'earthquake' | 'flood' | 'fire' | 'cyclone' | 'tsunami' | 'landslide' | 'volcano';
  title: string;
  location: string;
  coordinates: { lat: number; lng: number };
  severity: 'critical' | 'high' | 'medium' | 'low';
  timestamp: Date;
  description: string;
  affectedArea: string;
  casualties?: number;
  status: 'active' | 'monitoring' | 'resolved';
}

export interface Alert {
  id: string;
  disasterId: string;
  title: string;
  message: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  timestamp: Date;
  isNew: boolean;
  location: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  phone: string;
  location: {
    city: string;
    state: string;
    country: string;
    coordinates?: { lat: number; lng: number };
  };
  isAuthorized: boolean;
  avatar?: string;
  notificationPreferences: {
    email: boolean;
    sms: boolean;
    push: boolean;
  };
}

// Mock data for disasters
export const mockDisasters: Disaster[] = [
  {
    id: '1',
    type: 'earthquake',
    title: 'Earthquake in California',
    location: 'Los Angeles, California, USA',
    coordinates: { lat: 34.0522, lng: -118.2437 },
    severity: 'critical',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
    description: 'A 6.4 magnitude earthquake struck the greater Los Angeles area.',
    affectedArea: '150 km radius',
    casualties: 12,
    status: 'active',
  },
  {
    id: '2',
    type: 'flood',
    title: 'Flash Flood Warning',
    location: 'Mumbai, Maharashtra, India',
    coordinates: { lat: 19.076, lng: 72.8777 },
    severity: 'high',
    timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
    description: 'Heavy monsoon rains causing severe flooding in low-lying areas.',
    affectedArea: 'Mumbai Metropolitan Region',
    status: 'active',
  },
  {
    id: '3',
    type: 'fire',
    title: 'Wildfire Alert',
    location: 'Sydney, New South Wales, Australia',
    coordinates: { lat: -33.8688, lng: 151.2093 },
    severity: 'high',
    timestamp: new Date(Date.now() - 12 * 60 * 60 * 1000),
    description: 'Bushfire spreading rapidly due to dry conditions and strong winds.',
    affectedArea: '500 hectares',
    status: 'monitoring',
  },
  {
    id: '4',
    type: 'cyclone',
    title: 'Cyclone Approaching',
    location: 'Odisha, India',
    coordinates: { lat: 20.9517, lng: 85.0985 },
    severity: 'medium',
    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000),
    description: 'Cyclonic storm expected to make landfall within 48 hours.',
    affectedArea: 'Coastal Odisha',
    status: 'monitoring',
  },
  {
    id: '5',
    type: 'tsunami',
    title: 'Tsunami Watch',
    location: 'Tokyo, Japan',
    coordinates: { lat: 35.6762, lng: 139.6503 },
    severity: 'medium',
    timestamp: new Date(Date.now() - 48 * 60 * 60 * 1000),
    description: 'Minor tsunami waves detected following undersea earthquake.',
    affectedArea: 'Eastern Coast of Japan',
    status: 'resolved',
  },
  {
    id: '6',
    type: 'landslide',
    title: 'Landslide in Himalayas',
    location: 'Uttarakhand, India',
    coordinates: { lat: 30.0668, lng: 79.0193 },
    severity: 'low',
    timestamp: new Date(Date.now() - 72 * 60 * 60 * 1000),
    description: 'Minor landslide blocking mountain roads.',
    affectedArea: 'Chamoli District',
    status: 'resolved',
  },
];

// Mock alerts
export const mockAlerts: Alert[] = [
  {
    id: 'a1',
    disasterId: '1',
    title: 'CRITICAL: Earthquake Alert',
    message: 'A 6.4 magnitude earthquake has struck Los Angeles. Seek immediate shelter.',
    severity: 'critical',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
    isNew: true,
    location: 'Los Angeles, CA',
  },
  {
    id: 'a2',
    disasterId: '2',
    title: 'Flood Warning',
    message: 'Flash flood warning issued for Mumbai. Avoid low-lying areas.',
    severity: 'high',
    timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
    isNew: true,
    location: 'Mumbai, India',
  },
  {
    id: 'a3',
    disasterId: '3',
    title: 'Fire Alert',
    message: 'Bushfire spreading near Sydney suburbs. Evacuation may be required.',
    severity: 'high',
    timestamp: new Date(Date.now() - 12 * 60 * 60 * 1000),
    isNew: false,
    location: 'Sydney, Australia',
  },
  {
    id: 'a4',
    disasterId: '4',
    title: 'Cyclone Advisory',
    message: 'Cyclone expected to approach Odisha coast. Prepare emergency supplies.',
    severity: 'medium',
    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000),
    isNew: false,
    location: 'Odisha, India',
  },
];

// Mock user
export const mockUser: User = {
  id: 'u1',
  name: 'John Doe',
  email: 'john.doe@example.com',
  phone: '+1 555-0123',
  location: {
    city: 'Los Angeles',
    state: 'California',
    country: 'USA',
    coordinates: { lat: 34.0522, lng: -118.2437 },
  },
  isAuthorized: false,
  notificationPreferences: {
    email: true,
    sms: true,
    push: true,
  },
};

// Authorized user for testing
export const mockAuthorizedUser: User = {
  ...mockUser,
  id: 'u2',
  name: 'Sarah Admin',
  email: 'sarah.admin@gov.org',
  isAuthorized: true,
};

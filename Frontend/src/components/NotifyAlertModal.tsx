import { useState } from 'react';
import { 
  AlertTriangle, 
  Upload, 
  X, 
  MapPin, 
  Image as ImageIcon,
  Shield,
  XCircle,
  Loader2,
  Building // Added icon for state
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle,
  DialogDescription 
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/contexts/AuthContext';

interface NotifyAlertModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

// --- UPDATED GEOCODING FUNCTION ---
async function getCoordinates(city: string, state: string) {
  try {
    // Combine for a better search query
    const query = `${city}, ${state}`;
    
    // Call OpenStreetMap API
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`
    );
    const data = await response.json();

    if (data && data.length > 0) {
      return {
        lat: parseFloat(data[0].lat),
        lng: parseFloat(data[0].lon)
      };
    }
    return null; 
  } catch (error) {
    console.error("Geocoding failed:", error);
    return null;
  }
}

const alertTypes = [
  { value: 'earthquake', label: 'Earthquake' },
  { value: 'flood', label: 'Flood' },
  { value: 'fire', label: 'Wildfire' },
  { value: 'cyclone', label: 'Cyclone' },
  { value: 'tsunami', label: 'Tsunami' },
  { value: 'landslide', label: 'Landslide' },
  { value: 'volcano', label: 'Volcanic Activity' },
];

const severityLevels = [
  { value: 'critical', label: 'Critical', color: 'text-red-400' },
  { value: 'high', label: 'High', color: 'text-orange-400' },
  { value: 'medium', label: 'Medium', color: 'text-yellow-400' },
  { value: 'low', label: 'Low', color: 'text-green-400' },
];

export default function NotifyAlertModal({ isOpen, onClose, onSuccess }: NotifyAlertModalProps) {
  const { user } = useAuth();
  const { toast } = useToast();
  
  // --- UPDATED STATE ---
  const [formData, setFormData] = useState({
    type: '',
    severity: '',
    city: '',    // Changed from location to city
    state: '',   // Added state
    description: '',
  });
  
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  if (!user?.isAuthorized) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="glass-strong border-border/50 max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <XCircle className="w-5 h-5" />
              Access Denied
            </DialogTitle>
            <DialogDescription>
              You are not authorized to create alerts.
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-8 text-center">
            <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-destructive/10 border border-destructive/30 flex items-center justify-center">
              <Shield className="w-10 h-10 text-destructive" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Authorization Required</h3>
            <p className="text-sm text-muted-foreground mb-6">
              Only authorized government officials and verified responders can submit disaster alerts. 
              Contact your administrator to request authorization.
            </p>
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
      setErrors(prev => ({ ...prev, image: '' }));
    }
  };

  const removeImage = () => {
    setImage(null);
    setImagePreview(null);
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.type) newErrors.type = 'Alert type is required';
    if (!formData.severity) newErrors.severity = 'Severity level is required';
    if (!formData.city.trim()) newErrors.city = 'City is required';
    if (!formData.state.trim()) newErrors.state = 'State is required';
    if (!formData.description.trim()) newErrors.description = 'Description is required';
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validate()) return;
    
    setIsSubmitting(true);
    
    try {
      const token = localStorage.getItem('token');
      
      // 1. Get Coordinates using City and State
      const coords = await getCoordinates(formData.city, formData.state);
      
      // 2. Merge City and State into one string for the 'location' field
      // This ensures the Dashboard can display it easily (e.g., "Mumbai, Maharashtra")
      const mergedLocation = `${formData.city}, ${formData.state}`;

      const payload = {
        title: `${formData.severity.toUpperCase()} Alert: ${formData.type.charAt(0).toUpperCase() + formData.type.slice(1)}`,
        type: formData.type,
        severity: formData.severity,
        location: mergedLocation, // Sending merged string
        message: formData.description,
        coordinates: coords || { lat: 0, lng: 0 },
      };

      const response = await fetch('http://localhost:5000/api/alerts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error('Failed to submit alert');
      }

      toast({
        title: "Alert Submitted",
        description: `Alert for ${mergedLocation} broadcasted successfully.`,
      });
      
      // Reset form
      setFormData({ type: '', severity: '', city: '', state: '', description: '' });
      setImage(null);
      setImagePreview(null);
      
      if (onSuccess) onSuccess();
      onClose();

    } catch (error) {
      console.error(error);
      toast({
        variant: "destructive",
        title: "Submission Failed",
        description: "Could not connect to the server. Please try again.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="glass-strong border-border/50 max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-primary" />
            Submit Disaster Alert
          </DialogTitle>
          <DialogDescription>
            Submit a verified disaster alert for your location. All submissions are reviewed before broadcast.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          {/* Alert Type */}
          <div className="space-y-2">
            <Label>Alert Type *</Label>
            <Select 
              value={formData.type} 
              onValueChange={(value) => {
                setFormData(prev => ({ ...prev, type: value }));
                setErrors(prev => ({ ...prev, type: '' }));
              }}
            >
              <SelectTrigger className={`bg-secondary ${errors.type ? 'border-destructive' : ''}`}>
                <SelectValue placeholder="Select disaster type" />
              </SelectTrigger>
              <SelectContent>
                {alertTypes.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.type && <p className="text-sm text-destructive">{errors.type}</p>}
          </div>

          {/* Severity Level */}
          <div className="space-y-2">
            <Label>Severity Level *</Label>
            <Select 
              value={formData.severity}
              onValueChange={(value) => {
                setFormData(prev => ({ ...prev, severity: value }));
                setErrors(prev => ({ ...prev, severity: '' }));
              }}
            >
              <SelectTrigger className={`bg-secondary ${errors.severity ? 'border-destructive' : ''}`}>
                <SelectValue placeholder="Select severity level" />
              </SelectTrigger>
              <SelectContent>
                {severityLevels.map((level) => (
                  <SelectItem key={level.value} value={level.value}>
                    <span className={level.color}>{level.label}</span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.severity && <p className="text-sm text-destructive">{errors.severity}</p>}
          </div>

          {/* Location - SPLIT INTO CITY AND STATE */}
          <div className="space-y-2">
            <Label>Location *</Label>
            <div className="grid grid-cols-2 gap-3">
              {/* City Input */}
              <div className="space-y-1">
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="City / District"
                    value={formData.city}
                    onChange={(e) => {
                      setFormData(prev => ({ ...prev, city: e.target.value }));
                      setErrors(prev => ({ ...prev, city: '' }));
                    }}
                    className={`pl-10 bg-secondary ${errors.city ? 'border-destructive' : ''}`}
                  />
                </div>
                {errors.city && <p className="text-xs text-destructive">{errors.city}</p>}
              </div>

              {/* State Input */}
              <div className="space-y-1">
                <div className="relative">
                  <Building className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="State"
                    value={formData.state}
                    onChange={(e) => {
                      setFormData(prev => ({ ...prev, state: e.target.value }));
                      setErrors(prev => ({ ...prev, state: '' }));
                    }}
                    className={`pl-10 bg-secondary ${errors.state ? 'border-destructive' : ''}`}
                  />
                </div>
                {errors.state && <p className="text-xs text-destructive">{errors.state}</p>}
              </div>
            </div>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label>Description *</Label>
            <Textarea
              placeholder="Provide detailed description of the disaster..."
              value={formData.description}
              onChange={(e) => {
                setFormData(prev => ({ ...prev, description: e.target.value }));
                setErrors(prev => ({ ...prev, description: '' }));
              }}
              className={`bg-secondary min-h-[100px] ${errors.description ? 'border-destructive' : ''}`}
            />
            {errors.description && <p className="text-sm text-destructive">{errors.description}</p>}
          </div>

          {/* Image Upload */}
          <div className="space-y-2">
            <Label>Proof Image (Optional)</Label>
            
            {imagePreview ? (
              <div className="relative rounded-lg overflow-hidden border border-border">
                <img 
                  src={imagePreview} 
                  alt="Preview" 
                  className="w-full h-48 object-cover"
                />
                <button
                  type="button"
                  onClick={removeImage}
                  className="absolute top-2 right-2 p-1.5 rounded-full bg-background/80 hover:bg-background transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <label className={`flex flex-col items-center justify-center h-40 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${
                errors.image ? 'border-destructive' : 'border-border hover:border-primary/50'
              }`}>
                <ImageIcon className="w-10 h-10 text-muted-foreground mb-2" />
                <span className="text-sm text-muted-foreground">Click to upload image</span>
                <span className="text-xs text-muted-foreground mt-1">PNG, JPG up to 10MB</span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageChange}
                  className="hidden"
                />
              </label>
            )}
            {errors.image && <p className="text-sm text-destructive">{errors.image}</p>}
          </div>

          {/* Submit Button */}
          <div className="flex gap-3 pt-4">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1">
              Cancel
            </Button>
            <Button type="submit" className="flex-1 glow-primary" disabled={isSubmitting}>
              {isSubmitting ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Submitting...
                </div>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Submit Alert
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
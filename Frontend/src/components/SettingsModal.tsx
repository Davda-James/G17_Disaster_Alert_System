import { useState, useEffect } from 'react';
import { 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Save, 
  Loader2, 
  Building 
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const { user, updateUser } = useAuth();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  
  // State for validation errors
  const [errors, setErrors] = useState<{ phone?: string }>({});

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    city: '',
    state: ''
  });

  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name || '',
        email: user.email || '',
        phone: user.phone || '',
        city: user.location?.city || '',
        state: user.location?.state || ''
      });
      setErrors({}); // Clear errors when opening
    }
  }, [user, isOpen]);

  // --- 1. Validation Logic (Same as Signup) ---
  const validatePhone = (phone: string) => {
    // Strictly check for exactly 10 digits
    return /^\d{10}$/.test(phone);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // --- 2. Check before submitting ---
    if (!validatePhone(formData.phone)) {
      setErrors({ phone: "Please enter a valid 10-digit phone number" });
      return; // Stop here
    }

    setIsLoading(true);
    setErrors({}); // Clear previous errors

    try {
      const payload = {
        name: formData.name,
        phone: formData.phone,
        location: {
          city: formData.city,
          state: formData.state,
          country: "India"
        }
      };
      
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:5000/api/user/${user?.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) throw new Error('Failed to update profile');

      const updatedUserData = await response.json();
      await updateUser(updatedUserData); 

      toast({
        title: "Profile Updated",
        description: "Your information has been successfully saved.",
      });
      
      onClose();
    } catch (error) {
      console.error(error);
      toast({
        variant: "destructive",
        title: "Update Failed",
        description: "Could not save changes. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="glass-strong border-border/50 sm:max-w-[500px] p-0 overflow-hidden gap-0">
        
        <div className="p-6 border-b border-border/50 bg-secondary/30">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-xl">
              <User className="w-5 h-5 text-primary" />
              Account Settings
            </DialogTitle>
          </DialogHeader>
        </div>

        <div className="p-6 max-h-[70vh] overflow-y-auto">
          <form id="settings-form" onSubmit={handleSubmit} className="space-y-6">
            
            {/* Name Section */}
            <div className="space-y-2">
              <Label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Personal Information
              </Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="pl-10 bg-secondary/50 border-border/50 focus:bg-background transition-all"
                  placeholder="Full Name"
                />
              </div>
            </div>

            {/* Contact Section */}
            <div className="space-y-4">
              <Label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Contact Details
              </Label>
              
              <div className="grid gap-4">
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    value={formData.email}
                    disabled
                    className="pl-10 bg-secondary/50 border-border/50 opacity-70 cursor-not-allowed"
                  />
                </div>

                <div className="space-y-1">
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      value={formData.phone}
                      onChange={(e) => {
                        setFormData({...formData, phone: e.target.value});
                        // Clear error while typing
                        if (errors.phone) setErrors({...errors, phone: undefined});
                      }}
                      className={`pl-10 bg-secondary/50 border-border/50 focus:bg-background transition-all ${
                        errors.phone ? 'border-destructive focus-visible:ring-destructive' : ''
                      }`}
                      placeholder="Phone Number"
                    />
                  </div>
                  {/* --- 3. Error Message Display --- */}
                  {errors.phone && (
                    <p className="text-xs text-destructive ml-1">{errors.phone}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Location Section */}
            <div className="space-y-4">
              <Label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Location
              </Label>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    value={formData.city}
                    onChange={(e) => setFormData({...formData, city: e.target.value})}
                    className="pl-10 bg-secondary/50 border-border/50 focus:bg-background transition-all"
                    placeholder="City"
                  />
                </div>
                <div className="relative">
                  <Building className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    value={formData.state}
                    onChange={(e) => setFormData({...formData, state: e.target.value})}
                    className="pl-10 bg-secondary/50 border-border/50 focus:bg-background transition-all"
                    placeholder="State"
                  />
                </div>
              </div>
            </div>

          </form>
        </div>

        <div className="p-6 border-t border-border/50 bg-secondary/30 flex justify-end gap-3">
          <Button variant="ghost" onClick={onClose} type="button">
            Cancel
          </Button>
          <Button 
            type="submit" 
            form="settings-form"
            className="glow-primary min-w-[120px]"
            disabled={isLoading}
          >
            {isLoading ? (
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Saving...
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Save className="w-4 h-4" />
                Save Changes
              </div>
            )}
          </Button>
        </div>

      </DialogContent>
    </Dialog>
  );
}
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Shield, Eye, EyeOff, Mail, Phone, Lock, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";

export default function LoginPage() {
  const [loginType, setLoginType] = useState<'email' | 'phone'>('email');
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<{ identifier?: string; password?: string }>({});
  
  const { login } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  const validateEmail = (email: string) => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  };

  const validatePhone = (phone: string) => {
    const digits = phone.replace(/\D/g, '');
    return digits.length === 10;
  };

  const validate = () => {
    const newErrors: typeof errors = {};

    if (!identifier) {
      newErrors.identifier = loginType === 'email' ? 'Email is required' : 'Phone number is required';
    } else if (loginType === 'email' && !validateEmail(identifier)) {
      newErrors.identifier = 'Please enter a valid email address';
    } else if (loginType === 'phone' && !validatePhone(identifier)) {
      newErrors.identifier = 'Please enter a valid 10-digit phone number';
    }

    if (!password) {
      newErrors.password = 'Password is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validate()) return;

    setIsLoading(true);
    
    const success = await login(identifier, password);
    
    setIsLoading(false);

    if (success) {
      toast({
        title: "Welcome back!",
        description: "You have successfully logged in.",
      });
      navigate('/dashboard');
    } else {
      toast({
        variant: "destructive",
        title: "Login failed",
        description: "Invalid credentials. Please try again.",
      });
    }
  };

  const isFormValid = identifier && password && !errors.identifier && !errors.password;

  return (
    <div className="min-h-screen flex hero-gradient">
      {/* Left side - Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="w-full max-w-md"
        >
          <Link to="/" className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground mb-8 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to home
          </Link>

          <div className="flex items-center gap-3 mb-8">
            <div className="p-2 rounded-xl bg-primary/20 border border-primary/30">
              <Shield className="w-6 h-6 text-primary" />
            </div>
            <span className="text-xl font-bold">DisasterWatch</span>
          </div>

          <h1 className="text-3xl font-bold mb-2">Welcome back</h1>
          <p className="text-muted-foreground mb-8">Sign in to access your dashboard</p>

          {/* Login Type Toggle */}
          <div className="flex gap-2 p-1 rounded-lg bg-secondary mb-6">
            <button
              type="button"
              onClick={() => { setLoginType('email'); setIdentifier(''); setErrors({}); }}
              className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-md transition-all ${
                loginType === 'email' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground'
              }`}
            >
              <Mail className="w-4 h-4" />
              Email
            </button>
            <button
              type="button"
              onClick={() => { setLoginType('phone'); setIdentifier(''); setErrors({}); }}
              className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-md transition-all ${
                loginType === 'phone' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground'
              }`}
            >
              <Phone className="w-4 h-4" />
              Phone
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="identifier">
                {loginType === 'email' ? 'Email Address' : 'Phone Number'}
              </Label>
              <div className="relative">
                {loginType === 'email' ? (
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                ) : (
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                )}
                <Input
                  id="identifier"
                  type={loginType === 'email' ? 'email' : 'tel'}
                  placeholder={loginType === 'email' ? 'you@example.com' : '1234567890'}
                  value={identifier}
                  onChange={(e) => { setIdentifier(e.target.value); setErrors(prev => ({ ...prev, identifier: undefined })); }}
                  className={`pl-10 h-12 bg-secondary border-border input-focus ${errors.identifier ? 'border-destructive' : ''}`}
                />
              </div>
              {errors.identifier && (
                <p className="text-sm text-destructive">{errors.identifier}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setErrors(prev => ({ ...prev, password: undefined })); }}
                  className={`pl-10 pr-10 h-12 bg-secondary border-border input-focus ${errors.password ? 'border-destructive' : ''}`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="text-sm text-destructive">{errors.password}</p>
              )}
            </div>

            <Button 
              type="submit" 
              className="w-full h-12 text-base glow-primary"
              disabled={!isFormValid || isLoading}
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                  Signing in...
                </div>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>

          <p className="text-center text-muted-foreground mt-6">
            Don't have an account?{' '}
            <Link to="/signup" className="text-primary hover:underline font-medium">
              Sign up
            </Link>
          </p>

          {/* Demo credentials hint */}
          <div className="mt-8 p-4 rounded-lg bg-secondary/50 border border-border/50">
            <p className="text-xs text-muted-foreground text-center">
              <strong>Demo:</strong> Use any email with password <code className="text-primary">password123</code>
              <br />
              Or <code className="text-primary">admin@gov.org</code> / <code className="text-primary">admin123</code> for authorized access
            </p>
          </div>
        </motion.div>
      </div>

      {/* Right side - Decorative */}
      <div className="hidden lg:flex flex-1 items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-transparent to-transparent" />
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="relative z-10 text-center p-12"
        >
          <div className="w-32 h-32 mx-auto mb-8 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center glow-primary">
            <Shield className="w-16 h-16 text-primary" />
          </div>
          <h2 className="text-2xl font-bold mb-4">Secure Access</h2>
          <p className="text-muted-foreground max-w-sm">
            Government-grade security ensures your data and alerts are protected at all times.
          </p>
        </motion.div>
      </div>
    </div>
  );
}

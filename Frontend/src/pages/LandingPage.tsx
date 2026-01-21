import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Shield, AlertTriangle, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import GlobeBackground from "@/components/GlobeBackground";

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden hero-gradient">
      {/* Globe Background */}
      <div className="absolute inset-0 opacity-60">
        <GlobeBackground showMarkers={true} />
      </div>

      {/* Radial gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/50 to-background pointer-events-none" />

      {/* Navigation */}
      <nav className="relative z-10">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-3"
            >
              <div className="p-2 rounded-xl bg-primary/20 border border-primary/30">
                <Shield className="w-6 h-6 text-primary" />
              </div>
              <span className="text-xl font-bold text-foreground">DisasterWatch</span>
            </motion.div>

            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-4"
            >
              <Link to="/login">
                <Button variant="ghost" className="text-muted-foreground hover:text-foreground">
                  Login
                </Button>
              </Link>
              <Link to="/signup">
                <Button className="glow-primary">
                  Get Started
                </Button>
              </Link>
            </motion.div>
          </div>
        </div>
      </nav>

      {/* Hero Content */}
      <main className="relative z-10 container mx-auto px-6 pt-20 pb-32">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mb-6"
          >
            <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass text-sm text-muted-foreground">
              <AlertTriangle className="w-4 h-4 text-primary" />
              Real-time Global Disaster Monitoring
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-5xl md:text-7xl font-bold mb-6 leading-tight"
          >
            <span className="text-foreground">Disaster Management</span>
            <br />
            <span className="gradient-text">& Alert System</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-xl md:text-2xl text-muted-foreground mb-12 max-w-2xl mx-auto"
          >
            Real-time disaster alerts based on your location. Stay informed, stay safe.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <Link to="/login">
              <Button size="lg" variant="outline" className="min-w-[160px] h-14 text-lg border-border/50 hover:bg-secondary">
                Login
              </Button>
            </Link>
            <Link to="/signup">
              <Button size="lg" className="min-w-[160px] h-14 text-lg glow-primary">
                Sign Up
              </Button>
            </Link>
          </motion.div>
        </div>

        {/* Feature Pills */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="mt-24 flex flex-wrap justify-center gap-4"
        >
          {[
            { icon: MapPin, text: "Location-Based Alerts" },
            { icon: Shield, text: "Government-Grade Security" },
            { icon: AlertTriangle, text: "Real-Time Monitoring" },
          ].map((feature, i) => (
            <div
              key={i}
              className="flex items-center gap-2 px-4 py-2 rounded-full glass text-sm text-muted-foreground"
            >
              <feature.icon className="w-4 h-4 text-primary" />
              {feature.text}
            </div>
          ))}
        </motion.div>
      </main>

      {/* Stats Section */}
      <section className="relative z-10 border-t border-border/30">
        <div className="container mx-auto px-6 py-16">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { value: "50K+", label: "Active Users" },
              { value: "24/7", label: "Monitoring" },
              { value: "190+", label: "Countries" },
              { value: "<1min", label: "Alert Time" },
            ].map((stat, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8 + i * 0.1 }}
                className="text-center"
              >
                <div className="text-3xl md:text-4xl font-bold gradient-text mb-2">
                  {stat.value}
                </div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

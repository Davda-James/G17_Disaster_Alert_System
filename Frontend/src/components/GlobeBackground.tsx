import { Suspense, useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Sphere, OrbitControls, useTexture, Html } from '@react-three/drei';
import * as THREE from 'three';
import { Alert } from '@/components/Alert'; 

const GLOBE_RADIUS = 2;

// 1. Math Helper remains the same
function latLngToVector3(lat: number, lng: number, radius: number): [number, number, number] {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lng + 180) * (Math.PI / 180);

  const x = -(radius * Math.sin(phi) * Math.cos(theta));
  const z = radius * Math.sin(phi) * Math.sin(theta);
  const y = radius * Math.cos(phi);

  return [x, y, z];
}

// 2. Main Content Group (Earth + Markers)
// We rotate THIS group so everything moves together
function GlobeContent({ alerts }: { alerts: Alert[] }) {
  const groupRef = useRef<THREE.Group>(null);
  
  // Load Texture
  const [colorMap, bumpMap, specularMap] = useTexture([
    'https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg',
    'https://unpkg.com/three-globe/example/img/earth-topology.png',
    'https://unpkg.com/three-globe/example/img/earth-water.png',
  ]);

  // ROTATION LOGIC: Rotates the entire group (Earth + Markers)
  useFrame(() => {
    if (groupRef.current) {
      groupRef.current.rotation.y += 0.0005; // Adjust speed here
    }
  });

  // Calculate markers once
  const markers = useMemo(() => {
    return alerts
      .filter(alert => alert.coordinates && alert.coordinates.lat)
      .map(alert => {
        const position = latLngToVector3(
          alert.coordinates!.lat, 
          alert.coordinates!.lng, 
          GLOBE_RADIUS + 0.02 
        );
        
        let color = '#ef4444'; 
        if (alert.severity === 'medium') color = '#eab308';
        if (alert.severity === 'low') color = '#22c55e';

        return { ...alert, position, color };
      });
  }, [alerts]);

  return (
    <group ref={groupRef}>
      {/* 1. The Earth Sphere */}
      <Sphere args={[GLOBE_RADIUS, 64, 64]}>
        <meshPhongMaterial
          map={colorMap}
          bumpMap={bumpMap}
          bumpScale={0.05}
          specularMap={specularMap}
          specular={new THREE.Color('grey')}
          shininess={5}
        />
        {/* Atmosphere Glow */}
        <Sphere args={[GLOBE_RADIUS + 0.05, 64, 64]}>
          <meshBasicMaterial
            color="#4db2ff"
            transparent
            opacity={0.1}
            side={THREE.BackSide}
            blending={THREE.AdditiveBlending}
          />
        </Sphere>
      </Sphere>

      {/* 2. The Markers (Now children of the same group) */}
      {markers.map((marker) => (
        <group key={marker.id} position={marker.position as [number, number, number]}>
          {/* Dot */}
          <Sphere args={[0.013, 16, 16]}>
             <meshBasicMaterial color={marker.color} toneMapped={false} />
          </Sphere>
          {/* Pulse/Glow */}
          <mesh>
             <sphereGeometry args={[0.013, 16, 16]} />
             <meshBasicMaterial color={marker.color} transparent opacity={0.4} />
          </mesh>
          
          {/* Label (Optional - un-comment if you want names floating) */}
          {/* <Html distanceFactor={10}>
            <div className="bg-black/80 text-white text-[8px] p-1 rounded hidden group-hover:block">
              {marker.location}
            </div>
          </Html> 
          */}
        </group>
      ))}
    </group>
  );
}

interface GlobeBackgroundProps {
  interactive?: boolean;
  showMarkers?: boolean;
  className?: string;
  alerts?: Alert[];
}

export default function GlobeBackground({ 
  interactive = false, 
  showMarkers = true,
  className = "",
  alerts = [] 
}: GlobeBackgroundProps) {
  return (
    <div className={`absolute inset-0 ${className}`}>
      <Suspense fallback={
        <div className="w-full h-full flex items-center justify-center bg-slate-900">
          <div className="text-blue-400 animate-pulse">Loading Globe...</div>
        </div>
      }>
        <Canvas
          camera={{ position: [0, 0, 5.5], fov: 45 }}
          gl={{ antialias: true, alpha: true }}
        >
          <ambientLight intensity={1.5} color="#ffffff" />
          <pointLight position={[10, 10, 10]} intensity={2} />
          <pointLight position={[-10, -10, -10]} intensity={1} color="#4db2ff" />
          
          {/* We render the Group Content */}
          <GlobeContent alerts={showMarkers ? alerts : []} />

          {interactive && (
            <OrbitControls
              enableZoom={true}
              enablePan={false}
              minDistance={3}
              maxDistance={10}
              rotateSpeed={0.5}
              autoRotate={false} // Disable OrbitControls rotation, we use manual group rotation now
            />
          )}
        </Canvas>
      </Suspense>
    </div>
  );
}
import { Suspense, useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, PerspectiveCamera } from "@react-three/drei";
import * as THREE from "three";

const AMBER = "#e8a54b";
const MINT = "#5dcea0";
const INK = "#e8ecf2";
const DEEP = "#0e1218";

function VenueFloor() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1.35, 0]} receiveShadow>
      <circleGeometry args={[6.5, 64]} />
      <meshStandardMaterial
        color="#121821"
        metalness={0.55}
        roughness={0.35}
        emissive={AMBER}
        emissiveIntensity={0.04}
      />
    </mesh>
  );
}

function StageRing() {
  const ref = useRef<THREE.Mesh>(null);
  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.rotation.z = clock.getElapsedTime() * 0.08;
  });

  return (
    <mesh ref={ref} rotation={[-Math.PI / 2, 0, 0]} position={[0, -1.33, 0]}>
      <ringGeometry args={[2.2, 2.35, 80]} />
      <meshStandardMaterial
        color={AMBER}
        emissive={AMBER}
        emissiveIntensity={0.55}
        metalness={0.7}
        roughness={0.25}
        side={THREE.DoubleSide}
      />
    </mesh>
  );
}

function Ticket({
  position,
  rotation,
  scale = 1,
  tone = AMBER,
}: {
  position: [number, number, number];
  rotation: [number, number, number];
  scale?: number;
  tone?: string;
}) {
  return (
    <Float speed={1.4} rotationIntensity={0.45} floatIntensity={0.55}>
      <group position={position} rotation={rotation} scale={scale}>
        <mesh castShadow>
          <boxGeometry args={[1.35, 0.85, 0.04]} />
          <meshStandardMaterial
            color="#1a2230"
            metalness={0.35}
            roughness={0.4}
            emissive={tone}
            emissiveIntensity={0.08}
          />
        </mesh>
        {/* accent stripe */}
        <mesh position={[0, 0.28, 0.025]}>
          <boxGeometry args={[1.15, 0.08, 0.01]} />
          <meshStandardMaterial
            color={tone}
            emissive={tone}
            emissiveIntensity={0.65}
            metalness={0.5}
            roughness={0.3}
          />
        </mesh>
        {/* QR-ish block */}
        <mesh position={[-0.35, -0.08, 0.025]}>
          <boxGeometry args={[0.32, 0.32, 0.01]} />
          <meshStandardMaterial
            color={INK}
            emissive={INK}
            emissiveIntensity={0.15}
            metalness={0.2}
            roughness={0.5}
          />
        </mesh>
      </group>
    </Float>
  );
}

function ParticleField({ count = 120 }: { count?: number }) {
  const points = useRef<THREE.Points>(null);
  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      arr[i * 3] = (Math.random() - 0.5) * 10;
      arr[i * 3 + 1] = Math.random() * 5 - 1;
      arr[i * 3 + 2] = (Math.random() - 0.5) * 8;
    }
    return arr;
  }, [count]);

  useFrame(({ clock }) => {
    if (!points.current) return;
    points.current.rotation.y = clock.getElapsedTime() * 0.02;
  });

  return (
    <points ref={points}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.035}
        color={AMBER}
        transparent
        opacity={0.55}
        sizeAttenuation
        depthWrite={false}
      />
    </points>
  );
}

function CameraRig() {
  useFrame(({ camera, clock }) => {
    const t = clock.getElapsedTime();
    camera.position.x = Math.sin(t * 0.18) * 0.55;
    camera.position.y = 0.9 + Math.sin(t * 0.25) * 0.12;
    camera.lookAt(0, 0.1, 0);
  });
  return null;
}

function Scene() {
  return (
    <>
      <color attach="background" args={[DEEP]} />
      <fog attach="fog" args={[DEEP, 6, 16]} />
      <PerspectiveCamera makeDefault position={[0, 1.1, 5.2]} fov={42} />
      <CameraRig />

      <ambientLight intensity={0.35} />
      <spotLight
        position={[3.5, 6, 2]}
        angle={0.45}
        penumbra={0.7}
        intensity={2.2}
        color={AMBER}
        castShadow
      />
      <pointLight position={[-3, 2, -2]} intensity={0.7} color={MINT} />
      <pointLight position={[0, 0.5, 2]} intensity={0.45} color={AMBER} />

      <VenueFloor />
      <StageRing />
      <ParticleField />

      <Ticket position={[0.2, 0.35, 0.2]} rotation={[-0.2, 0.45, 0.08]} scale={1.15} />
      <Ticket
        position={[-1.55, 0.55, -0.4]}
        rotation={[0.15, -0.55, -0.12]}
        scale={0.85}
        tone={MINT}
      />
      <Ticket
        position={[1.7, 0.2, -0.7]}
        rotation={[-0.35, 0.9, 0.05]}
        scale={0.75}
      />
      <Ticket
        position={[-0.4, 1.15, -1.2]}
        rotation={[0.4, 0.2, -0.2]}
        scale={0.55}
        tone={INK}
      />
    </>
  );
}

export default function LandingHeroScene() {
  return (
    <div className="landing-canvas" aria-hidden="true">
      <Canvas
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: false, powerPreference: "high-performance" }}
        shadows
      >
        <Suspense fallback={null}>
          <Scene />
        </Suspense>
      </Canvas>
    </div>
  );
}

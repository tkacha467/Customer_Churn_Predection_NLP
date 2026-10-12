import { useEffect, useRef } from 'react';
import * as THREE from 'three';

export default function VajraCanvas() {
  const containerRef = useRef(null);
  const scrollRef = useRef(0);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Check prefers-reduced-motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Scene setup
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x06080d, 0.035);

    const camera = new THREE.PerspectiveCamera(
      45,
      window.innerWidth / window.innerHeight,
      0.1,
      100
    );
    camera.position.set(0, 0, 10);

    const isMobile = window.matchMedia('(max-width: 767px)').matches;
    const renderer = new THREE.WebGLRenderer({
      powerPreference: 'high-performance',
      antialias: true,
      alpha: true,
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, isMobile ? 1.25 : 1.6));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    container.appendChild(renderer.domElement);

    // Subtle atmospheric ambient & key lights
    const ambientLight = new THREE.AmbientLight(0x0a1c22, 1.2);
    scene.add(ambientLight);

    const cyanPointLight = new THREE.PointLight(0x00f0ff, 3.5, 25);
    cyanPointLight.position.set(4, 3, 5);
    scene.add(cyanPointLight);

    const tealPointLight = new THREE.PointLight(0x00d2aa, 2.8, 25);
    tealPointLight.position.set(-4, -2, 4);
    scene.add(tealPointLight);

    const deepPurpleLight = new THREE.PointLight(0x2a164d, 1.5, 20);
    deepPurpleLight.position.set(0, 5, -3);
    scene.add(deepPurpleLight);

    // ─── VAJRA CENTRAL VORTEX RING (Torus swirl echoing logo geometry) ──────────
    const torusGroup = new THREE.Group();
    scene.add(torusGroup);
    torusGroup.position.set(isMobile ? 1.9 : 5.0, isMobile ? -1.8 : 0, isMobile ? -1.4 : -0.8);
    torusGroup.scale.setScalar(isMobile ? 0.4 : 0.76);

    // Primary Torus Swirl
    const torusGeo = new THREE.TorusGeometry(2.4, 0.42, 32, 120);
    const torusMat = new THREE.MeshPhysicalMaterial({
      color: 0x052329,
      emissive: 0x00373e,
      emissiveIntensity: 0.55,
      roughness: 0.18,
      metalness: 0.65,
      clearcoat: 0.9,
      clearcoatRoughness: 0.15,
      transmission: 0.28,
      transparent: true,
      opacity: 0.64,
    });
    const mainTorus = new THREE.Mesh(torusGeo, torusMat);
    torusGroup.add(mainTorus);

    // Secondary inner counter-twist ring
    const innerTorusGeo = new THREE.TorusGeometry(1.65, 0.18, 24, 90);
    const innerTorusMat = new THREE.MeshStandardMaterial({
      color: 0x00f0ff,
      emissive: 0x00c4cc,
      emissiveIntensity: 0.36,
      roughness: 0.25,
      transparent: true,
      opacity: 0.72,
      metalness: 0.85,
      wireframe: false,
    });
    const innerTorus = new THREE.Mesh(innerTorusGeo, innerTorusMat);
    torusGroup.add(innerTorus);

    // Outer subtle orbital glass ring
    const outerRingGeo = new THREE.RingGeometry(3.1, 3.16, 64);
    const outerRingMat = new THREE.MeshBasicMaterial({
      color: 0x00e5ff,
      transparent: true,
      opacity: 0.15,
      side: THREE.DoubleSide,
    });
    const outerRing = new THREE.Mesh(outerRingGeo, outerRingMat);
    torusGroup.add(outerRing);

    // ─── FLOATING CLAY & GLASS GEOMETRIC SHAPES (VAJRA Motifs) ────────────────
    const floatersGroup = new THREE.Group();
    scene.add(floatersGroup);
    floatersGroup.position.x = isMobile ? 0.8 : 1.1;
    floatersGroup.scale.setScalar(isMobile ? 0.65 : 0.88);

    const clayMaterial = new THREE.MeshStandardMaterial({
      color: 0x0f1c24,
      roughness: 0.45,
      metalness: 0.25,
    });

    const glowClayMaterial = new THREE.MeshStandardMaterial({
      color: 0x082e38,
      emissive: 0x00b4c6,
      emissiveIntensity: 0.4,
      roughness: 0.35,
      metalness: 0.4,
    });

    // 6 Floating tactile shapes around the world
    const floaters = [];
    const geometries = [
      new THREE.IcosahedronGeometry(0.55, 1),
      new THREE.TorusGeometry(0.65, 0.22, 16, 40),
      new THREE.SphereGeometry(0.48, 24, 24),
      new THREE.CylinderGeometry(0.3, 0.3, 0.6, 24),
      new THREE.IcosahedronGeometry(0.7, 0),
      new THREE.TorusGeometry(0.5, 0.16, 16, 32),
    ];

    const floaterOffsets = [
      { x: -4.8, y: 1.8, z: -1.5, rx: 0.005, ry: 0.008 },
      { x: 4.6, y: 2.2, z: -2.0, rx: -0.006, ry: 0.004 },
      { x: -3.8, y: -2.4, z: -1.0, rx: 0.007, ry: -0.005 },
      { x: 4.2, y: -2.0, z: -1.8, rx: -0.004, ry: -0.007 },
      { x: -1.6, y: 3.5, z: -3.0, rx: 0.003, ry: 0.006 },
      { x: 2.2, y: -3.2, z: -2.5, rx: 0.005, ry: 0.003 },
    ];

    geometries.forEach((geo, i) => {
      const mesh = new THREE.Mesh(geo, i % 2 === 0 ? glowClayMaterial : clayMaterial);
      const conf = floaterOffsets[i];
      mesh.position.set(conf.x, conf.y, conf.z);
      floatersGroup.add(mesh);
      floaters.push({ mesh, conf, basePos: mesh.position.clone() });
    });

    // ─── AMBIENT LUMINESCENT PARTICLES (Calm, sparse, non-distracting) ─────────
    const particleCount = isMobile ? 44 : 100;
    const particleGeo = new THREE.BufferGeometry();
    const particlePos = new Float32Array(particleCount * 3);
    const particleScales = new Float32Array(particleCount);

    for (let i = 0; i < particleCount; i++) {
      particlePos[i * 3 + 0] = (Math.random() - 0.5) * 22;
      particlePos[i * 3 + 1] = (Math.random() - 0.5) * 20;
      particlePos[i * 3 + 2] = (Math.random() - 0.5) * 16;
      particleScales[i] = Math.random() * 0.8 + 0.3;
    }

    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePos, 3));
    particleGeo.setAttribute('scale', new THREE.BufferAttribute(particleScales, 1));

    const particleMat = new THREE.PointsMaterial({
      color: 0x00f0ff,
      size: 0.07,
      transparent: true,
      opacity: 0.55,
      blending: THREE.AdditiveBlending,
    });

    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);

    // ─── MOUSE PARALLAX TRACKING ──────────────────────────────────────────────
    const mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
    const handleMouseMove = (e) => {
      const normX = (e.clientX / window.innerWidth) * 2 - 1;
      const normY = -(e.clientY / window.innerHeight) * 2 + 1;
      mouse.targetX = normX * 0.45;
      mouse.targetY = normY * 0.45;
    };
    window.addEventListener('mousemove', handleMouseMove, { passive: true });

    const handleScroll = () => {
      const scrollable = document.documentElement.scrollHeight - window.innerHeight;
      scrollRef.current = scrollable > 0 ? Math.min(Math.max(window.scrollY / scrollable, 0), 1) : 0;
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();

    // ─── RESIZE HANDLER ───────────────────────────────────────────────────────
    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, window.innerWidth < 768 ? 1.25 : 1.6));
    };
    window.addEventListener('resize', handleResize);

    // ─── ANIMATION LOOP ───────────────────────────────────────────────────────
    let animationFrameId;
    const animationStart = performance.now();
    let isVisible = !document.hidden;

    const handleVisibilityChange = () => {
      isVisible = !document.hidden;
      if (prefersReducedMotion) return;
      if (isVisible) animationFrameId = requestAnimationFrame(animate);
      else cancelAnimationFrame(animationFrameId);
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    const animate = () => {
      if (!isVisible) return;
      animationFrameId = requestAnimationFrame(animate);

      const elapsedTime = (performance.now() - animationStart) / 1000;
      const progress = scrollRef.current || 0;

      // Mouse lerp
      mouse.x += (mouse.targetX - mouse.x) * 0.05;
      mouse.y += (mouse.targetY - mouse.y) * 0.05;

      if (!prefersReducedMotion) {
        // Continuous organic rotation of main motif
        torusGroup.rotation.x = 0.55 + Math.sin(elapsedTime * 0.3) * 0.12 + progress * 1.8;
        torusGroup.rotation.y = elapsedTime * 0.22 + progress * 2.4;
        torusGroup.rotation.z = Math.cos(elapsedTime * 0.25) * 0.08 + progress * 1.2;

        innerTorus.rotation.x = -elapsedTime * 0.35;
        innerTorus.rotation.y = elapsedTime * 0.45;

        // Camera scroll choreography:
        // Hero: close (Z=9)
        // Middle: zooms back (Z=12.5), tilts, pans
        // Pricing / CTA: settles at calm depth (Z=10.2)
        const targetZ = 8.5 + progress * 4.2 - (progress > 0.8 ? (progress - 0.8) * 3 : 0);
        const targetY = -progress * 3.2 + mouse.y * 0.8;
        const targetX = Math.sin(progress * Math.PI) * 1.4 + mouse.x * 0.8;

        camera.position.z += (targetZ - camera.position.z) * 0.08;
        camera.position.y += (targetY - camera.position.y) * 0.08;
        camera.position.x += (targetX - camera.position.x) * 0.08;
        camera.lookAt(0, -progress * 1.5, 0);

        // Floaters subtle bobbing
        floaters.forEach(({ mesh, conf, basePos }, index) => {
          mesh.rotation.x += conf.rx;
          mesh.rotation.y += conf.ry;
          mesh.position.y = basePos.y + Math.sin(elapsedTime * 1.2 + index * 1.1) * 0.18;
          mesh.position.x = basePos.x + Math.cos(elapsedTime * 0.8 + index) * 0.12;
        });

        // Drift particles slowly
        particles.rotation.y = elapsedTime * 0.03 + progress * 0.4;
        particles.rotation.x = Math.sin(elapsedTime * 0.02) * 0.05;

        // Dynamic light orbits
        cyanPointLight.position.x = Math.sin(elapsedTime * 0.6) * 5;
        cyanPointLight.position.y = Math.cos(elapsedTime * 0.5) * 4;
        tealPointLight.position.x = -Math.cos(elapsedTime * 0.4) * 5;
        tealPointLight.position.y = -Math.sin(elapsedTime * 0.5) * 3;
      }

      renderer.render(scene, camera);
    };

    if (prefersReducedMotion) renderer.render(scene, camera);
    else animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', handleResize);
      document.removeEventListener('visibilitychange', handleVisibilityChange);

      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
      torusGeo.dispose();
      torusMat.dispose();
      innerTorusGeo.dispose();
      innerTorusMat.dispose();
      outerRingGeo.dispose();
      outerRingMat.dispose();
      particleGeo.dispose();
      particleMat.dispose();
      geometries.forEach((g) => g.dispose());
      clayMaterial.dispose();
      glowClayMaterial.dispose();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="vajra-webgl-wrapper"
      aria-hidden="true"
    />
  );
}


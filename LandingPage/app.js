/**
 * MOVEXA // BIOMETRIC AI GYM COACH — INTERACTIVE ENGINE
 * Responsive Kinematic Simulator, Real-Time Angles & Web Audio FX
 */

document.addEventListener('DOMContentLoaded', () => {
  // ── SOUND FX SYNTHESIZER (WEB AUDIO API) ──
  class CyberAudio {
    constructor() {
      this.ctx = null;
      this.enabled = true;
    }

    init() {
      if (!this.ctx) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        this.ctx = new AudioContext();
      }
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
    }

    playTone(freq, type = 'sine', duration = 0.08, gainVal = 0.05) {
      if (!this.enabled) return;
      try {
        this.init();
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = type;
        osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
        gain.gain.setValueAtTime(gainVal, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + duration);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start();
        osc.stop(this.ctx.currentTime + duration);
      } catch (e) {
        // Fallback
      }
    }

    click() {
      this.playTone(850, 'sine', 0.04, 0.04);
    }

    success() {
      if (!this.enabled) return;
      this.playTone(523.25, 'triangle', 0.08, 0.06); // C5
      setTimeout(() => this.playTone(659.25, 'triangle', 0.12, 0.06), 70); // E5
      setTimeout(() => this.playTone(1046.50, 'sine', 0.2, 0.08), 140); // C6
    }

    warning() {
      if (!this.enabled) return;
      this.playTone(330, 'sawtooth', 0.1, 0.06);
      setTimeout(() => this.playTone(290, 'sawtooth', 0.15, 0.06), 80);
    }
  }

  const sfx = new CyberAudio();

  // Sound Toggle in Nav
  const soundToggleBtn = document.getElementById('sound-toggle');
  if (soundToggleBtn) {
    soundToggleBtn.addEventListener('click', () => {
      sfx.enabled = !sfx.enabled;
      soundToggleBtn.classList.toggle('active', sfx.enabled);
      soundToggleBtn.innerHTML = sfx.enabled ? '🔊 SFX: ON' : '🔇 SFX: OFF';
      if (sfx.enabled) sfx.success();
    });
  }

  // ── HERO CANVAS BACKGROUND (BIOMETRIC PARTICLES) ──
  const heroCanvas = document.getElementById('hero-canvas');
  if (heroCanvas) {
    const ctx = heroCanvas.getContext('2d');
    let width = heroCanvas.width = heroCanvas.offsetWidth;
    let height = heroCanvas.height = heroCanvas.offsetHeight;

    window.addEventListener('resize', () => {
      width = heroCanvas.width = heroCanvas.offsetWidth;
      height = heroCanvas.height = heroCanvas.offsetHeight;
    });

    const particles = [];
    const numParticles = 40;
    let mouse = { x: width / 2, y: height / 2, active: false };

    heroCanvas.addEventListener('mousemove', (e) => {
      const rect = heroCanvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
      mouse.active = true;
    });

    heroCanvas.addEventListener('mouseleave', () => {
      mouse.active = false;
    });

    for (let i = 0; i < numParticles; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.7,
        vy: (Math.random() - 0.5) * 0.7,
        radius: Math.random() * 2 + 1,
        alpha: Math.random() * 0.6 + 0.2
      });
    }

    function renderHeroCanvas() {
      ctx.clearRect(0, 0, width, height);

      // Grid lines
      ctx.strokeStyle = 'rgba(0, 240, 255, 0.025)';
      ctx.lineWidth = 1;
      const step = 60;
      for (let x = 0; x < width; x += step) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += step) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // Connect particles
      for (let i = 0; i < particles.length; i++) {
        const p1 = particles[i];
        p1.x += p1.vx;
        p1.y += p1.vy;

        if (p1.x < 0 || p1.x > width) p1.vx *= -1;
        if (p1.y < 0 || p1.y > height) p1.vy *= -1;

        ctx.beginPath();
        ctx.arc(p1.x, p1.y, p1.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 240, 255, ${p1.alpha})`;
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dist = Math.hypot(p1.x - p2.x, p1.y - p2.y);
          if (dist < 130) {
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = `rgba(0, 240, 255, ${(1 - dist / 130) * 0.15})`;
            ctx.stroke();
          }
        }

        if (mouse.active) {
          const mouseDist = Math.hypot(p1.x - mouse.x, p1.y - mouse.y);
          if (mouseDist < 160) {
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(mouse.x, mouse.y);
            ctx.strokeStyle = `rgba(0, 255, 136, ${(1 - mouseDist / 160) * 0.35})`;
            ctx.stroke();
          }
        }
      }

      requestAnimationFrame(renderHeroCanvas);
    }
    renderHeroCanvas();
  }

  // ── BIOMETRIC SIMULATOR ENGINE ──
  const EXERCISE_PROTOCOLS = {
    squats: {
      name: 'SQUATS',
      target: 'Quads & Glutes',
      primaryLabel: 'KNEE FLEXION',
      secondaryLabel: 'BACK POSTURE',
      angleMin: 70,
      angleMax: 165,
      optimalAngle: 85,
      shallowThreshold: 105,
      targetReps: 10,
      guidance: "Knee flexion angle must break parallel (<90°) while keeping the torso inclination aligned and heels grounded."
    },
    pushups: {
      name: 'PUSH-UPS',
      target: 'Chest & Core',
      primaryLabel: 'ELBOW ANGLE',
      secondaryLabel: 'SPINE ALIGNMENT',
      angleMin: 80,
      angleMax: 165,
      optimalAngle: 90,
      shallowThreshold: 110,
      targetReps: 12,
      guidance: "Descend until elbows reach 90° flexion. Maintain a straight plank line from ears through hips to ankles."
    },
    curls: {
      name: 'BICEPS CURLS',
      target: 'Biceps Brachii',
      primaryLabel: 'ELBOW FLEXION',
      secondaryLabel: 'SHOULDER LOCK',
      angleMin: 40,
      angleMax: 160,
      optimalAngle: 50,
      shallowThreshold: 90,
      targetReps: 10,
      guidance: "Flex elbows past 45° with shoulders locked against your ribs. Avoid any backward torso swing momentum."
    },
    shoulder_press: {
      name: 'SHOULDER PRESS',
      target: 'Deltoids & Triceps',
      primaryLabel: 'OVERHEAD LOCK',
      secondaryLabel: 'LUMBAR ARCH',
      angleMin: 80,
      angleMax: 175,
      optimalAngle: 170,
      shallowThreshold: 140,
      targetReps: 8,
      guidance: "Drive the weight vertically to a full 180° lockout directly over your crown without overarching your lumbar spine."
    },
    lunges: {
      name: 'LUNGES',
      target: 'Glutes & Quads',
      primaryLabel: 'LEAD KNEE',
      secondaryLabel: 'TORSO BALANCE',
      angleMin: 85,
      angleMax: 160,
      optimalAngle: 90,
      shallowThreshold: 115,
      targetReps: 10,
      guidance: "Step into a square 90° knee stride. Keep the torso vertical to ensure optimal balance and pelvic alignment."
    }
  };

  let currentExKey = 'squats';
  let isPlaying = true;
  let faultMode = false;
  let repPhase = 0;
  let repDirection = 1;
  let completedReps = 3;
  let scrubValue = 0;
  let lastTime = performance.now();

  const simCanvas = document.getElementById('sim-canvas');
  const simCtx = simCanvas ? simCanvas.getContext('2d') : null;

  // DOM Elements for Simulator HUD
  const primaryAngleVal = document.getElementById('sim-angle-primary');
  const primaryAngleLabel = document.getElementById('sim-label-primary');
  const primaryStatusBadge = document.getElementById('sim-badge-primary');
  const secondaryAngleVal = document.getElementById('sim-angle-secondary');
  const secondaryAngleLabel = document.getElementById('sim-label-secondary');
  const secondaryStatusBadge = document.getElementById('sim-badge-secondary');
  const repCounterEl = document.getElementById('sim-rep-count');
  const repRingProgress = document.getElementById('sim-ring-progress');
  const ringPctText = document.getElementById('sim-ring-pct');
  const scrubSlider = document.getElementById('sim-scrub-slider');
  const playBtn = document.getElementById('sim-play-btn');
  const faultBtn = document.getElementById('sim-fault-btn');
  const guidanceNameEl = document.getElementById('sim-guidance-name');
  const guidanceDescEl = document.getElementById('sim-guidance-desc');

  // Exercise Tab Switching
  const exTabs = document.querySelectorAll('.sim-tab-btn');
  exTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      sfx.click();
      exTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentExKey = tab.dataset.exercise;
      completedReps = 0;
      updateRepCounter();
      
      const proto = EXERCISE_PROTOCOLS[currentExKey];
      if (guidanceNameEl) guidanceNameEl.textContent = proto.name;
      if (guidanceDescEl) guidanceDescEl.textContent = proto.guidance;
    });
  });

  // Play / Pause Toggle
  if (playBtn) {
    playBtn.addEventListener('click', () => {
      sfx.click();
      isPlaying = !isPlaying;
      playBtn.innerHTML = isPlaying ? '⏸ PAUSE' : '▶ RESUME';
      playBtn.style.background = isPlaying ? 'var(--cyan)' : 'rgba(255,255,255,0.1)';
      playBtn.style.color = isPlaying ? '#030712' : 'var(--text-main)';
    });
  }

  // Fault Mode Toggle
  if (faultBtn) {
    faultBtn.addEventListener('click', () => {
      sfx.click();
      faultMode = !faultMode;
      faultBtn.classList.toggle('active', faultMode);
      faultBtn.innerHTML = faultMode ? '⚠️ FAULT SIM: ACTIVE' : '⚪ SIMULATE FORM FAULT';
      if (faultMode) {
        sfx.warning();
      } else {
        sfx.success();
      }
    });
  }

  // Scrub Slider
  if (scrubSlider) {
    scrubSlider.addEventListener('input', (e) => {
      isPlaying = false;
      if (playBtn) {
        playBtn.innerHTML = '▶ RESUME';
        playBtn.style.background = 'rgba(255,255,255,0.1)';
        playBtn.style.color = 'var(--text-main)';
      }
      scrubValue = parseFloat(e.target.value);
      repPhase = scrubValue;
    });
  }

  // Update Rep Counter & SVG Progress Ring
  function updateRepCounter() {
    const proto = EXERCISE_PROTOCOLS[currentExKey];
    if (repCounterEl) repCounterEl.textContent = completedReps;
    const pct = Math.min(100, Math.round((completedReps / proto.targetReps) * 100));
    if (ringPctText) ringPctText.textContent = `${pct}%`;
    if (repRingProgress) {
      const circumference = 226;
      const offset = circumference - (pct / 100) * circumference;
      repRingProgress.style.strokeDashoffset = offset;
    }
  }

  // ── SIMULATOR KINEMATICS RENDERER (CANVAS) ──
  function resizeSimCanvas() {
    if (!simCanvas) return;
    simCanvas.width = simCanvas.offsetWidth;
    simCanvas.height = simCanvas.offsetHeight;
  }
  window.addEventListener('resize', resizeSimCanvas);
  resizeSimCanvas();

  function drawBiometricSkeleton(ctx, w, h, ex, phase, isFault) {
    ctx.clearRect(0, 0, w, h);

    // Grid backdrop
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.04)';
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    for (let y = 0; y < h; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Biometric Target Crosshairs
    const cx = w * 0.5;
    const cy = h * 0.52;
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.15)';
    ctx.strokeRect(w * 0.15, h * 0.08, w * 0.7, h * 0.84);

    let joints = {};
    let primaryAngleDeg = 160;
    let secondaryAngleDeg = 175;

    if (ex === 'squats') {
      const depth = isFault ? phase * 0.55 : phase;
      const hipDrop = depth * (h * 0.18);
      const kneePush = depth * (w * 0.07);

      joints = {
        head: { x: cx, y: cy - h * 0.32 + hipDrop * 0.7 },
        neck: { x: cx, y: cy - h * 0.26 + hipDrop * 0.7 },
        shoulder: { x: cx - (isFault ? w * 0.04 : 0), y: cy - h * 0.22 + hipDrop * 0.7 },
        elbow: { x: cx + w * 0.06, y: cy - h * 0.14 + hipDrop * 0.7 },
        wrist: { x: cx + w * 0.09, y: cy - h * 0.06 + hipDrop * 0.7 },
        hip: { x: cx - (isFault ? w * 0.08 : w * 0.04), y: cy - h * 0.04 + hipDrop },
        knee: { x: cx + w * 0.05 + kneePush, y: cy + h * 0.16 + hipDrop * 0.1 },
        ankle: { x: cx + w * 0.03, y: cy + h * 0.35 }
      };

      primaryAngleDeg = Math.round(165 - (depth * 95));
      secondaryAngleDeg = Math.round(175 - (isFault ? depth * 40 : depth * 15));
    } 
    else if (ex === 'pushups') {
      const depth = isFault ? phase * 0.45 : phase;
      const bodyDrop = depth * (h * 0.14);
      const hipSag = isFault ? depth * (h * 0.08) : 0;

      joints = {
        head: { x: cx - w * 0.25, y: cy - bodyDrop + 10 },
        neck: { x: cx - w * 0.20, y: cy - bodyDrop },
        shoulder: { x: cx - w * 0.15, y: cy - bodyDrop },
        elbow: { x: cx - w * 0.15, y: cy - h * 0.1 + bodyDrop * 0.2 },
        wrist: { x: cx - w * 0.15, y: cy + h * 0.1 },
        hip: { x: cx + w * 0.05, y: cy - bodyDrop * 0.8 + hipSag },
        knee: { x: cx + w * 0.22, y: cy - bodyDrop * 0.5 },
        ankle: { x: cx + w * 0.35, y: cy + h * 0.08 }
      };

      primaryAngleDeg = Math.round(165 - (depth * 75));
      secondaryAngleDeg = Math.round(180 - (isFault ? 32 : 5));
    }
    else if (ex === 'curls') {
      const curl = phase;
      const swing = isFault ? phase * (w * 0.08) : 0;

      joints = {
        head: { x: cx - swing * 0.5, y: cy - h * 0.3 },
        neck: { x: cx - swing * 0.5, y: cy - h * 0.24 },
        shoulder: { x: cx - swing * 0.5, y: cy - h * 0.18 },
        elbow: { x: cx - swing * 0.3, y: cy },
        wrist: { 
          x: cx + Math.sin(curl * Math.PI * 0.7) * (w * 0.12),
          y: cy + Math.cos(curl * Math.PI * 0.7) * (h * 0.14)
        },
        hip: { x: cx - swing, y: cy + h * 0.06 },
        knee: { x: cx, y: cy + h * 0.22 },
        ankle: { x: cx, y: cy + h * 0.36 }
      };

      primaryAngleDeg = Math.round(160 - (curl * 120));
      secondaryAngleDeg = Math.round(175 - (isFault ? swing * 2.5 : 2));
    }
    else if (ex === 'shoulder_press') {
      const press = phase;
      const arch = isFault ? phase * (w * 0.06) : 0;

      joints = {
        head: { x: cx + arch * 0.5, y: cy - h * 0.28 },
        neck: { x: cx + arch * 0.4, y: cy - h * 0.22 },
        shoulder: { x: cx, y: cy - h * 0.16 },
        elbow: { 
          x: cx + w * 0.12 - (press * w * 0.04),
          y: cy - h * 0.06 - (press * h * 0.15)
        },
        wrist: { 
          x: cx + w * 0.12 - (press * w * 0.07),
          y: cy - h * 0.12 - (press * h * 0.22)
        },
        hip: { x: cx - arch, y: cy + h * 0.08 },
        knee: { x: cx, y: cy + h * 0.24 },
        ankle: { x: cx, y: cy + h * 0.38 }
      };

      primaryAngleDeg = Math.round(85 + (press * 90));
      secondaryAngleDeg = Math.round(180 - (isFault ? 25 : 3));
    }
    else if (ex === 'lunges') {
      const depth = isFault ? phase * 0.6 : phase;
      const drop = depth * (h * 0.15);

      joints = {
        head: { x: cx, y: cy - h * 0.3 + drop * 0.8 },
        neck: { x: cx, y: cy - h * 0.24 + drop * 0.8 },
        shoulder: { x: cx, y: cy - h * 0.18 + drop * 0.8 },
        elbow: { x: cx, y: cy - h * 0.08 + drop * 0.8 },
        wrist: { x: cx, y: cy + drop * 0.8 },
        hip: { x: cx, y: cy + drop },
        knee: { x: cx + w * 0.12, y: cy + h * 0.12 + drop * 0.2 },
        ankle: { x: cx + w * 0.12, y: cy + h * 0.32 },
        backKnee: { x: cx - w * 0.12, y: cy + h * 0.18 + drop * 0.8 },
        backAnkle: { x: cx - w * 0.20, y: cy + h * 0.32 }
      };

      primaryAngleDeg = Math.round(155 - (depth * 65));
      secondaryAngleDeg = Math.round(180 - (isFault ? 28 : 4));
    }

    const bones = [
      ['head', 'neck'],
      ['neck', 'shoulder'],
      ['shoulder', 'elbow'],
      ['elbow', 'wrist'],
      ['shoulder', 'hip'],
      ['hip', 'knee'],
      ['knee', 'ankle']
    ];

    if (joints.backKnee) {
      bones.push(['hip', 'backKnee'], ['backKnee', 'backAnkle']);
    }

    ctx.shadowBlur = 12;
    ctx.shadowColor = isFault ? 'rgba(255, 51, 102, 0.8)' : 'rgba(0, 240, 255, 0.8)';
    ctx.strokeStyle = isFault ? 'var(--danger-crimson)' : 'var(--cyan)';
    ctx.lineWidth = 3.5;
    ctx.lineCap = 'round';

    bones.forEach(([j1, j2]) => {
      if (joints[j1] && joints[j2]) {
        ctx.beginPath();
        ctx.moveTo(joints[j1].x, joints[j1].y);
        ctx.lineTo(joints[j2].x, joints[j2].y);
        ctx.stroke();
      }
    });

    ctx.shadowBlur = 15;
    Object.entries(joints).forEach(([name, pos]) => {
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 5, 0, Math.PI * 2);
      ctx.fillStyle = isFault ? '#FF3366' : '#00FF88';
      ctx.fill();
      ctx.strokeStyle = '#FFFFFF';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      ctx.fillStyle = 'rgba(255,255,255,0.4)';
      ctx.font = '9px JetBrains Mono';
      ctx.fillText(name.toUpperCase(), pos.x + 8, pos.y + 3);
    });

    if (joints.knee && joints.hip && joints.ankle) {
      const k = joints.knee;
      ctx.beginPath();
      ctx.arc(k.x, k.y, 22, 0, Math.PI * 1.5);
      ctx.strokeStyle = isFault ? 'rgba(255, 51, 102, 0.7)' : 'rgba(0, 255, 136, 0.7)';
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.fillStyle = isFault ? '#FF3366' : '#00FF88';
      ctx.font = 'bold 12px Space Grotesk';
      ctx.fillText(`${primaryAngleDeg}°`, k.x - 38, k.y - 10);
    }

    const scanY = (performance.now() * 0.12) % h;
    ctx.beginPath();
    ctx.moveTo(0, scanY);
    ctx.lineTo(w, scanY);
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.35)';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    ctx.shadowBlur = 0;

    return { primaryAngleDeg, secondaryAngleDeg };
  }

  // ── SIMULATOR ANIMATION LOOP ──
  function runSimulatorLoop(time) {
    const delta = (time - lastTime) / 1000;
    lastTime = time;

    const proto = EXERCISE_PROTOCOLS[currentExKey];

    if (isPlaying) {
      repPhase += delta * 0.8 * repDirection;
      if (repPhase >= 1) {
        repPhase = 1;
        repDirection = -1;
      } else if (repPhase <= 0) {
        repPhase = 0;
        repDirection = 1;
        completedReps = (completedReps % proto.targetReps) + 1;
        updateRepCounter();
        sfx.click();

        if (completedReps === proto.targetReps) {
          sfx.success();
        }
      }
      scrubValue = repPhase;
      if (scrubSlider) scrubSlider.value = scrubValue;
    }

    if (simCtx && simCanvas) {
      const angles = drawBiometricSkeleton(
        simCtx, 
        simCanvas.width, 
        simCanvas.height, 
        currentExKey, 
        repPhase, 
        faultMode
      );

      if (primaryAngleVal) primaryAngleVal.textContent = angles.primaryAngleDeg;
      if (primaryAngleLabel) primaryAngleLabel.textContent = proto.primaryLabel;

      if (secondaryAngleVal) secondaryAngleVal.textContent = angles.secondaryAngleDeg;
      if (secondaryAngleLabel) secondaryAngleLabel.textContent = proto.secondaryLabel;

      if (primaryStatusBadge) {
        if (faultMode) {
          primaryStatusBadge.className = 'angle-status-badge badge-danger';
          primaryStatusBadge.textContent = '▲ FORM WARNING';
        } else if (angles.primaryAngleDeg <= proto.optimalAngle + 10) {
          primaryStatusBadge.className = 'angle-status-badge badge-optimal';
          primaryStatusBadge.textContent = '● OPTIMAL RANGE';
        } else {
          primaryStatusBadge.className = 'angle-status-badge badge-warning';
          primaryStatusBadge.textContent = '● IN PROGRESS';
        }
      }

      if (secondaryStatusBadge) {
        if (faultMode) {
          secondaryStatusBadge.className = 'angle-status-badge badge-danger';
          secondaryStatusBadge.textContent = '✖ DEVIATION';
        } else {
          secondaryStatusBadge.className = 'angle-status-badge badge-optimal';
          secondaryStatusBadge.textContent = '● STABLE';
        }
      }
    }

    requestAnimationFrame(runSimulatorLoop);
  }
  requestAnimationFrame(runSimulatorLoop);

  // ── INTERACTIVE 3D CARD TILT ON MOUSEMOVE ──
  const tiltCards = document.querySelectorAll('.protocol-card');
  tiltCards.forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      const rotateX = ((y - centerY) / centerY) * -10;
      const rotateY = ((x - centerX) / centerX) * 10;

      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-6px)`;
    });

    card.addEventListener('mouseleave', () => {
      card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)';
    });
  });

  updateRepCounter();
});

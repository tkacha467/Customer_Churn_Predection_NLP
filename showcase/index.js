document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------------------
    // 1. Navigation Scroll & Progress Bar
    // -------------------------------------------------------------------------
    const progressBar = document.getElementById('progressBar');
    window.addEventListener('scroll', () => {
        const winScroll = document.documentElement.scrollTop || document.body.scrollTop;
        const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrolled = (winScroll / height) * 100;
        progressBar.style.width = scrolled + '%';
        
        // Highlight active navbar link
        const slides = document.querySelectorAll('.slide');
        let currentActive = 'hero';
        slides.forEach(slide => {
            const slideTop = slide.offsetTop;
            if (winScroll >= slideTop - 200) {
                currentActive = slide.getAttribute('id');
            }
        });
        
        const navLinks = document.querySelectorAll('.nav-links a');
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${currentActive}`) {
                link.classList.add('active');
            }
        });
    });

    // -------------------------------------------------------------------------
    // 2. Intersection Observer (Scroll Reveal Animations)
    // -------------------------------------------------------------------------
    const observerOptions = {
        root: null,
        threshold: 0.15,
        rootMargin: "0px"
    };

    const slideObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active-slide');
            }
        });
    }, observerOptions);

    const slides = document.querySelectorAll('.slide');
    slides.forEach(slide => {
        slideObserver.observe(slide);
    });

    // -------------------------------------------------------------------------
    // 3. Ambient Particle Canvas Animation
    // -------------------------------------------------------------------------
    const canvas = document.getElementById('particleCanvas');
    const ctx = canvas.getContext('2d');
    
    let particlesArray = [];
    const numberOfParticles = 40;
    
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();
    
    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 2 + 1;
            this.speedX = Math.random() * 0.4 - 0.2;
            this.speedY = Math.random() * 0.4 - 0.2;
            this.opacity = Math.random() * 0.5 + 0.1;
        }
        
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            
            // Re-wrap bounds
            if (this.x > canvas.width) this.x = 0;
            if (this.x < 0) this.x = canvas.width;
            if (this.y > canvas.height) this.y = 0;
            if (this.y < 0) this.y = canvas.height;
        }
        
        draw() {
            ctx.fillStyle = `rgba(0, 242, 254, ${this.opacity})`;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    
    function initParticles() {
        particlesArray = [];
        for (let i = 0; i < numberOfParticles; i++) {
            particlesArray.push(new Particle());
        }
    }
    
    function animateParticles() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        particlesArray.forEach(p => {
            p.update();
            p.draw();
        });
        
        // Draw connection lines
        for (let i = 0; i < particlesArray.length; i++) {
            for (let j = i; j < particlesArray.length; j++) {
                const dx = particlesArray[i].x - particlesArray[j].x;
                const dy = particlesArray[i].y - particlesArray[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < 120) {
                    ctx.strokeStyle = `rgba(127, 0, 255, ${(1 - (distance / 120)) * 0.08})`;
                    ctx.lineWidth = 0.5;
                    ctx.beginPath();
                    ctx.moveTo(particlesArray[i].x, particlesArray[i].y);
                    ctx.lineTo(particlesArray[j].x, particlesArray[j].y);
                    ctx.stroke();
                }
            }
        }
        
        requestAnimationFrame(animateParticles);
    }
    
    initParticles();
    animateParticles();

    // -------------------------------------------------------------------------
    // 4. Interactive Simulation Engine
    // -------------------------------------------------------------------------
    // DOM Controls
    const recencyRange = document.getElementById('recencyRange');
    const recencyVal = document.getElementById('recencyVal');
    const frequencyRange = document.getElementById('frequencyRange');
    const frequencyVal = document.getElementById('frequencyVal');
    
    const segmentButtons = document.querySelectorAll('.segment-btn');
    const starButtons = document.querySelectorAll('.sim-star-btn');
    
    // DOM Outputs
    const simRiskVal = document.getElementById('simRiskVal');
    const simChurnVal = document.getElementById('simChurnVal');
    const simConsistencyVal = document.getElementById('simConsistencyVal');
    const simIntegrityVal = document.getElementById('simIntegrityVal');
    const simDecisionLog = document.getElementById('simDecisionLog');
    
    const circleProgress = document.getElementById('circleProgress');
    const circleRadius = 70;
    const circleCircumference = 2 * Math.PI * circleRadius; // ~439.82
    
    circleProgress.style.strokeDasharray = circleCircumference;
    circleProgress.style.strokeDashoffset = circleCircumference;
    
    // State variables
    let currentRecency = 90;
    let currentFrequency = 1;
    let currentSentiment = "NEUTRAL";
    let currentRating = 3;

    // Recency input handler
    recencyRange.addEventListener('input', (e) => {
        currentRecency = parseInt(e.target.value);
        recencyVal.innerText = `${currentRecency} days`;
        updateSimulation();
    });

    // Frequency input handler
    frequencyRange.addEventListener('input', (e) => {
        currentFrequency = parseInt(e.target.value);
        frequencyVal.innerText = `${currentFrequency} ${currentFrequency === 1 ? 'order' : 'orders'}`;
        updateSimulation();
    });

    // Sentiment segments click handler
    segmentButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            segmentButtons.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentSentiment = e.target.getAttribute('data-sentiment');
            
            // Set text label representation
            const textRepresentations = {
                "POSITIVE": "Positive",
                "NEUTRAL": "Neutral",
                "NEGATIVE": "Negative"
            };
            document.getElementById('sentimentVal').innerText = textRepresentations[currentSentiment];
            updateSimulation();
        });
    });

    // Star selector click handler
    starButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const selectedRate = parseInt(e.target.getAttribute('data-rate'));
            currentRating = selectedRate;
            
            // Highlight selected stars
            starButtons.forEach(star => {
                const starRate = parseInt(star.getAttribute('data-rate'));
                if (starRate <= selectedRate) {
                    star.classList.add('active');
                } else {
                    star.classList.remove('active');
                }
            });
            
            document.getElementById('ratingVal').innerText = `${currentRating} ${currentRating === 1 ? 'Star' : 'Stars'}`;
            updateSimulation();
        });
    });

    // Risk calculation engine
    function updateSimulation() {
        // 1. Churn probability (XGBoost)
        // High Recency (days inactive) increases churn risk
        // Low Frequency (fewer purchases) increases churn risk
        const recencyComponent = currentRecency / 365.0; // max 1.0
        const frequencyComponent = 1.0 / currentFrequency; // 1 to 0.1
        
        let churnProb = (recencyComponent * 0.7) + (frequencyComponent * 0.3);
        churnProb = Math.min(1.0, Math.max(0.0, churnProb)); // bound

        // 2. Review Integrity Mismatch
        let isMismatch = false;
        let consistency = "Match";
        let integrity = "Genuine";
        
        if (currentSentiment === "NEUTRAL") {
            consistency = "No Strong Sentiment";
            integrity = "No Clear Mismatch";
            isMismatch = false;
        } else if (currentRating >= 4 && currentSentiment === "NEGATIVE") {
            consistency = "Mismatch";
            integrity = "Suspicious";
            isMismatch = true;
        } else if (currentRating <= 2 && currentSentiment === "POSITIVE") {
            consistency = "Mismatch";
            integrity = "Suspicious";
            isMismatch = true;
        }

        // 3. Fused Risk Score
        // Formula: Risk Score = 0.6 * ChurnProb + 0.4 * MismatchFlag
        const mismatchWeight = isMismatch ? 1.0 : 0.0;
        const totalRisk = (churnProb * 0.6) + (mismatchWeight * 0.4);
        const totalRiskPct = Math.round(totalRisk * 100);

        // Update UI Outputs
        simRiskVal.innerText = `${totalRiskPct}%`;
        simChurnVal.innerText = `${Math.round(churnProb * 100)}%`;
        simConsistencyVal.innerText = consistency;
        simIntegrityVal.innerText = integrity;
        
        // Update color formatting
        if (consistency === "Mismatch") {
            simConsistencyVal.className = "danger-text";
            simIntegrityVal.className = "danger-text";
        } else if (consistency === "No Strong Sentiment") {
            simConsistencyVal.className = "warning-text";
            simIntegrityVal.className = "warning-text";
        } else {
            simConsistencyVal.className = "success-text";
            simIntegrityVal.className = "success-text";
        }
        
        // Dynamic circular progress ring update
        const offset = circleCircumference - (totalRiskPct / 100) * circleCircumference;
        circleProgress.style.strokeDashoffset = offset;
        
        // Dynamic color shifting for progress ring
        if (totalRiskPct >= 75) {
            circleProgress.style.stroke = "var(--danger)";
            simRiskVal.className = "sim-risk-val danger-text";
        } else if (totalRiskPct >= 40) {
            circleProgress.style.stroke = "var(--warning)";
            simRiskVal.className = "sim-risk-val warning-text";
        } else {
            circleProgress.style.stroke = "var(--primary)";
            simRiskVal.className = "sim-risk-val cyan-glow";
        }

        // Generate custom dynamic decision logs
        let decisionExplanation = "";
        
        if (isMismatch) {
            decisionExplanation = `🚨 **HIGH RISK ANOMALY DETECTED**: The customer gave a rating of ${currentRating} stars but the textual review sentiment is classified as ${currentSentiment.toLowerCase()}. The fusion engine flagged this as a suspicious mismatch (+40% Risk).`;
        } else if (currentSentiment === "NEUTRAL") {
            decisionExplanation = `🛡️ **NEUTRAL SYSTEM ACCURACY**: The text sentiment is genuinely neutral ("${currentSentiment.toLowerCase()}"), which is treated as an independent state of no clear mismatch. It is not flagged as suspicious.`;
        } else {
            decisionExplanation = `✅ **GENUINE TRANSACTION PROFILE**: The customer gave a rating of ${currentRating} stars and their review text sentiment is perfectly consistent (${currentSentiment.toLowerCase()}). Review integrity is genuine.`;
        }

        if (churnProb > 0.7) {
            decisionExplanation += ` Additionally, the customer's high inactivity period (${currentRecency} days) raises severe XGBoost churn concern.`;
        } else if (churnProb < 0.3) {
            decisionExplanation += ` Their high transactional frequency (${currentFrequency} orders) reflects strong customer loyalty.`;
        }

        simDecisionLog.innerHTML = decisionExplanation;
    }

    // Set initial simulator state
    updateSimulation();
});

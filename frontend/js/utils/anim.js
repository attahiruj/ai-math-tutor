// anim.js - Pop-in, bounce animations
const ANIMATIONS = `
@keyframes popIn {
    0% { opacity: 0; transform: scale(0.3); }
    60% { opacity: 1; transform: scale(1.05); }
    100% { transform: scale(1); }
}

@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}

@keyframes slideUp {
    0% { opacity: 0; transform: translateY(30px); }
    100% { opacity: 1; transform: translateY(0); }
}

.animate-pop-in {
    animation: popIn 0.35s ease-out both;
}

.animate-bounce {
    animation: bounce 0.6s ease infinite;
}

.animate-slide-up {
    animation: slideUp 0.4s ease-out both;
}
`;

// Inject animation styles
const animStyleSheet = document.createElement('style');
animStyleSheet.textContent = ANIMATIONS;
document.head.appendChild(animStyleSheet);

Object.assign(window, { ANIMATIONS });

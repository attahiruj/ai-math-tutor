// app.js - Main app initialization + router
const { useState, useEffect, useRef } = React;

// ── i18n ─────────────────────────────────────────
const LANGS = {
    EN: {
        code: "EN", label: "English", flag: "🇬🇧", welcome: "Hello!", sub: "Ready to learn math?",
        start: "Let's Go!", choose: "Who is learning today?", question: "How many",
        doYouSee: "do you see?", correct: "Amazing!", wrong: "Try again!",
        next: "Next", keepGoing: "Keep going!", yourScore: "Your score",
        skills: "Skills", parentTitle: "Weekly Report", parentSub: "Here's how your child is doing",
        counting: "Counting", addition: "Addition", subtraction: "Subtraction",
        numberSense: "Number Sense", wordProblems: "Word Problems",
        silence: "Take your time…", tap: "Tap your answer below", report: "Parent Report",
    },
    FR: {
        code: "FR", label: "Français", flag: "🇫🇷", welcome: "Bonjour!", sub: "Prêt à apprendre les maths?",
        start: "Allons-y!", choose: "Qui apprend aujourd'hui?", question: "Combien de",
        doYouSee: "tu vois?", correct: "Bravo!", wrong: "Essaie encore!",
        next: "Suivant", keepGoing: "Continue!", yourScore: "Ton score",
        skills: "Compétences", parentTitle: "Rapport hebdomadaire", parentSub: "Voici les progrès de votre enfant",
        counting: "Compter", addition: "Addition", subtraction: "Soustraction",
        numberSense: "Sens des nombres", wordProblems: "Problèmes", report: "Rapport",
    },
    KIN: {
        code: "KIN", label: "Kinyarwanda", flag: "🇷🇼", welcome: "Muraho!", sub: "Witeguye kwiga imibare?",
        start: "Reka Tugende!", choose: "Ni nde wiga uyu munsi?", question: "Ni angahe",
        doYouSee: "ubona?", correct: "Byiza cyane!", wrong: "Gerageza nanone!",
        next: "Komeza", keepGoing: "Komeza!", yourScore: "Amanota yawe",
        skills: "Ubumenyi", parentTitle: "Raporo y'icyumweru", parentSub: "Uko umwana wawe akora",
        counting: "Kubara", addition: "Gukurikirana", subtraction: "Gukuramo",
        numberSense: "Kumva imibare", wordProblems: "Ibibazo", report: "Raporo",
    },
};

// ── Stars display ─────────────────────────────────────────
function Stars({ count, max = 3 }) {
    var stars = [];
    for (var i = 0; i < max; i++) {
        stars.push(
            React.createElement('svg', { key: i, width: 44, height: 44, viewBox: "0 0 54 54",
                style: { filter: i < count ? "drop-shadow(0 2px 6px rgba(245,200,80,0.5))" : "none" }
            },
                React.createElement('polygon', {
                    points: "27,4 33,20 51,20 37,31 42,48 27,38 12,48 17,31 3,20 21,20",
                    fill: i < count ? "oklch(84% 0.18 88)" : "#E5E0F5"
                })
            )
        );
    }
    return React.createElement('div', { style: { display: "flex", gap: 8, justifyContent: "center" } }, stars);
}

// ── Progress bar ─────────────────────────────────────────
function ProgressBar({ value, color, label }) {
    return React.createElement('div', { style: { width: "100%", marginBottom: 14 } },
        React.createElement('div', { style: { display: "flex", justifyContent: "space-between", marginBottom: 6 } },
            React.createElement('span', { style: { fontSize: 15, fontWeight: 700, color: "#1E1A33" } }, label),
            React.createElement('span', { style: { fontSize: 15, fontWeight: 800, color } }, Math.round(value * 100) + "%")
        ),
        React.createElement('div', { style: { height: 14, background: "#EDEAF8", borderRadius: 999, overflow: "hidden" } },
            React.createElement('div', {
                style: { height: "100%", width: (value * 100) + "%", background: color, borderRadius: 999, transition: "width 0.8s ease" }
            })
        )
    );
}

// ── Welcome Screen ──────────────────────────────────────
function WelcomeScreen({ lang, setLang, onNext }) {
    const t = LANGS[lang];
    const [pulse, setPulse] = useState(false);

    useEffect(function() {
        const id = setInterval(function() { setPulse(function(p) { return !p; }); }, 1800);
        return function() { clearInterval(id); };
    }, []);

    return React.createElement('div', { className: "screen", style: { background: "linear-gradient(160deg, #F4F1FF 0%, #EBF5FF 100%)", gap: 0 }, 'data-screen-label': "01 Welcome" },
        // Logo container
        React.createElement('div', { style: { width: 110, height: 110, borderRadius: "50%", background: "white", boxShadow: "0 8px 32px rgba(100,80,200,0.18)",
            display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 28,
            transform: pulse ? "scale(1.04)" : "scale(1)", transition: "transform 0.8s ease" }
        },
            React.createElement('svg', { width: 60, height: 60, viewBox: "0 0 60 60" },
                React.createElement('circle', { cx: 30, cy: 30, r: 28, fill: "oklch(68% 0.14 248)", opacity: 0.15 }),
                React.createElement('text', { x: 30, y: 38, textAnchor: "middle", fontSize: 32, fontFamily: "Nunito", fontWeight: 900, fill: "oklch(55% 0.18 248)" }, "1+2")
            )
        ),
        // Title
        React.createElement('div', { style: { textAlign: "center", marginBottom: 32 } },
            React.createElement('div', { style: { fontSize: 52, fontWeight: 900, color: "#1E1A33", lineHeight: 1.1, letterSpacing: -1 } }, "MathKids"),
            React.createElement('div', { style: { fontSize: 20, fontWeight: 600, color: "#8A85A5", marginTop: 8 } }, t.welcome + " — " + t.sub)
        ),
        // Language selector
        React.createElement('div', { style: { display: "flex", gap: 12, marginBottom: 40 } },
            Object.values(LANGS).map(function(l) {
                return React.createElement('button', {
                    key: l.code, onClick: function() { setLang(l.code); },
                    style: { padding: "10px 20px", borderRadius: 999,
                        border: lang === l.code ? "3px solid oklch(68% 0.14 248)" : "3px solid #E0DCF5",
                        background: lang === l.code ? "oklch(68% 0.14 248)" : "#fff", color: lang === l.code ? "#fff" : "#1E1A33",
                        fontFamily: "Nunito", fontSize: 16, fontWeight: 800, cursor: "pointer", transition: "all 0.2s" }
                }, l.flag + " " + l.code);
            })
        ),
        // Start button
        React.createElement('button', { className: "btn-primary", onClick: onNext, style: { fontSize: 26, padding: "20px 64px" } }, t.start),
        // Bottom hint
        React.createElement('div', { style: { position: "absolute", bottom: 24, fontSize: 14, color: "#B0ABCC", fontWeight: 600 } }, "Tap · Touch · Voice — works offline")
    );
}

// ── Main App ───────────────────────────────────────────
function App() {
    const [screen, setScreen] = useState("welcome");
    const [lang, setLang] = useState("EN");
    const [learner, setLearner] = useState(null);
    const [studentId, setStudentId] = useState(null);
    const [sessionId, setSessionId] = useState(null);
    const [currentItem, setCurrentItem] = useState(null);
    const [feedbackText, setFeedbackText] = useState("");
    const [questionIdx, setQuestionIdx] = useState(0);
    const [correct, setCorrect] = useState(false);
    const [streak, setStreak] = useState(0);
    const [silenceTimer, setSilenceTimer] = useState(10);

    const apiRef = useRef(new APIClient());

    // Silence countdown
    useEffect(function() {
        if (screen !== "activity") return;
        setSilenceTimer(10);
        const id = setInterval(function() {
            setSilenceTimer(function(t) {
                if (t <= 1) { clearInterval(id); return 0; }
                return t - 1;
            });
        }, 1000);
        return function() { clearInterval(id); };
    }, [screen, questionIdx]);

    const handleProfileSelect = function(profile) {
        if (!profile) return;
        setLearner(profile);
        setStudentId(profile.student_id);
        setSessionId(profile.session_id);
        setScreen("activity");
        loadNextItem(profile.student_id);
    };

    const loadNextItem = async function(sid) {
        try {
            const item = await apiRef.current.getNextItem(sid, lang.toLowerCase());
            setCurrentItem(item);
            setQuestionIdx(function(prev) { return prev + 1; });
        } catch (err) {
            console.error("Failed to load item:", err);
        }
    };

    const handleAnswer = async function(choice) {
        if (!currentItem) return;
        try {
            const result = await apiRef.current.submitTap(studentId, sessionId, currentItem.id, choice);
            setCorrect(result.correct);
            setFeedbackText(result.feedback_text);
            setStreak(function(prev) { return result.correct ? prev + 1 : 0; });
            setScreen("feedback");
        } catch (err) {
            console.error("Failed to submit answer:", err);
        }
    };

    const handleFeedbackNext = function() {
        setScreen("activity");
        loadNextItem(studentId);
    };

    const handleShowReport = function() { setScreen("report"); };
    const handleBackFromReport = function() { setScreen("activity"); };

    // Render current screen
    switch (screen) {
        case "welcome":
            return React.createElement(WelcomeScreen, { lang: lang, setLang: setLang, onNext: function() { setScreen("profile"); } });
        case "profile":
            return React.createElement(ProfileScreen, { lang: lang, onSelect: handleProfileSelect, api: apiRef.current });
        case "activity":
            return currentItem ? React.createElement(ActivityScreen, {
                lang: lang, learner: learner, item: currentItem, onAnswer: handleAnswer,
                questionIdx: questionIdx, silenceCountdown: silenceTimer, api: apiRef.current
            }) : React.createElement('div', { className: "screen" }, "Loading...");
        case "feedback":
            return React.createElement(FeedbackScreen, {
                lang: lang, correct: correct, feedbackText: feedbackText, streak: streak,
                onNext: handleFeedbackNext, onParent: handleShowReport
            });
        case "report":
            return React.createElement(ReportScreen, { lang: lang, learner: learner, onBack: handleBackFromReport, api: apiRef.current });
        default:
            return React.createElement('div', {}, "Unknown screen");
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    const root = document.getElementById('root');
    if (root) {
        ReactDOM.render(React.createElement(App), root);
    }
});

Object.assign(window, { LANGS: LANGS, Stars: Stars, ProgressBar: ProgressBar, WelcomeScreen: WelcomeScreen, App: App });

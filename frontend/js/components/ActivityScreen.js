// ActivityScreen.js - Math activity + visual rendering
const COLORS = {
    blue: "oklch(68% 0.14 248)",
    green: "oklch(72% 0.14 152)",
    yellow: "oklch(84% 0.14 88)",
    coral: "oklch(72% 0.14 30)",
    purple: "oklch(68% 0.14 295)",
    teal: "oklch(70% 0.14 196)",
};

function ActivityScreen({ lang, learner, item, onAnswer, questionIdx, silenceCountdown, api }) {
    const t = window.LANGS[lang];
    const [selected, setSelected] = React.useState(null);
    const [animObjs, setAnimObjs] = React.useState([]);

    React.useEffect(() => {
        setSelected(null);
        const meta = item.visual_meta || (() => {
            if (!item.visual) return null;
            const parts = item.visual.includes('?') ? item.visual.split('_') : item.visual.split('_');
            if (parts.length === 2 && !isNaN(parts[1])) {
                return { shape: parts[0], count: parseInt(parts[1], 10), layout: "scatter" };
            }
            return null;
        })();

        if (meta && meta.count > 0) {
            const { shape, count, layout } = meta;
            const positions = [];
            if (layout === "row") {
                for (let i = 0; i < count; i++) {
                    positions.push({ x: 30 + i * 58, y: 80, delay: i * 60, shape });
                }
            } else {
                const cols = Math.ceil(Math.sqrt(count * 1.5));
                for (let i = 0; i < count; i++) {
                    const col = i % cols;
                    const row = Math.floor(i / cols);
                    positions.push({
                        x: 60 + col * 85 + (Math.random() * 20 - 10),
                        y: 40 + row * 90 + (Math.random() * 16 - 8),
                        delay: i * 60,
                        shape,
                    });
                }
            }
            setAnimObjs(positions);
        } else {
            setAnimObjs([]);
        }
    }, [item.id]);

    const handleSelect = (val) => {
        if (selected !== null) return;
        setSelected(val);
        setTimeout(() => onAnswer(val), 700);
    };

    const canvasW = Math.min(window.innerWidth - 48, 500);
    const canvasH = 210;

    const stem = item[`stem_${lang.toLowerCase()}`] || item.stem_en;

    return React.createElement('div', {
        className: "screen",
        style: { background: "#F4F1FF", gap: 0, padding: "20px 24px" },
        'data-screen-label': "03 Counting Activity"
    },
        // Top bar
        React.createElement('div', {
            style: { width: "100%", maxWidth: 560, display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }
        },
            React.createElement('div', { style: { display: "flex", gap: 6, alignItems: "center" } },
                React.createElement('div', {
                    style: { width: 42, height: 42, borderRadius: "50%", background: learner?.color || COLORS.blue,
                        display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontWeight: 900, fontSize: 18 }
                }, learner?.avatar || "A"),
                React.createElement('div', { style: { fontWeight: 800, fontSize: 16, color: "#1E1A33" } }, learner?.name || "Learner")
            ),
            React.createElement('div', { style: { display: "flex", gap: 8 } },
                [0, 1, 2, 3].map(i =>
                    React.createElement('div', {
                        key: i,
                        style: { width: 12, height: 12, borderRadius: "50%",
                            background: i < questionIdx ? COLORS.green : i === questionIdx ? COLORS.blue : "#DDD8F5" }
                    })
                )
            ),
            silenceCountdown < 8 && React.createElement('div', {
                style: { fontSize: 14, color: COLORS.coral, fontWeight: 800 }
            }, `⏱ ${silenceCountdown}s`)
        ),
        // Question card
        React.createElement('div', {
            className: "card",
            style: { width: "100%", maxWidth: 560, marginBottom: 20, textAlign: "center" }
        },
            React.createElement('div', {
                style: { fontSize: 22, fontWeight: 700, color: "#8A85A5", marginBottom: 8 }
            }, stem),
            // Objects canvas
            React.createElement('div', {
                style: { position: "relative", height: canvasH, width: "100%", background: "oklch(96% 0.03 248)",
                    borderRadius: 16, overflow: "hidden", margin: "0 auto" }
            },
                animObjs.length > 0 ? animObjs.map((pos, i) =>
                    React.createElement('div', {
                        key: i,
                        style: { position: "absolute", left: pos.x, top: pos.y,
                            opacity: selected !== null ? 0.7 : 1,
                            animation: `popIn 0.35s ${pos.delay}ms both ease-out` }
                    },
                        React.createElement(window.ShapeIcon, { shape: pos.shape, color: COLORS.blue, size: 50 })
                    )
                ) : React.createElement('img', {
                    src: `${api.baseUrl}${item.visual_url || "/images/" + item.visual + ".png"}`,
                    style: { height: "100%", width: "100%", objectFit: "contain" },
                    alt: "Math problem"
                })
            ),
            React.createElement('div', {
                style: { fontSize: 15, color: "#B0ABCC", fontWeight: 600, marginTop: 12 }
            }, t.tap)
        ),
        // Answer choices
        React.createElement('div', {
            style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, width: "100%", maxWidth: 560 }
        },
            item.distractors.concat(item.answer_int).sort(() => Math.random() - 0.5).map(val => {
                const isCorrect = val === item.answer_int;
                let bg = "#fff", border = "#E0DCF5";
                if (selected !== null) {
                    if (val === selected && isCorrect) { bg = "oklch(72% 0.14 152)"; border = COLORS.green; }
                    else if (val === selected && !isCorrect) { bg = "oklch(85% 0.10 30)"; border = COLORS.coral; }
                    else if (isCorrect) { bg = "oklch(72% 0.14 152)"; border = COLORS.green; }
                }
                return React.createElement('button', {
                    key: val, onClick: () => handleSelect(val),
                    style: { padding: "18px 12px", borderRadius: 18,
                        border: `3px solid ${selected !== null && (val === selected || val === item.answer_int) ? border : "#E0DCF5"}`,
                        background: bg, fontFamily: "Nunito", fontSize: 36, fontWeight: 900,
                        color: (selected !== null && (val === selected || (val === item.answer_int && val !== selected))) ? "#fff" : "#1E1A33",
                        cursor: selected === null ? "pointer" : "default",
                        boxShadow: "0 4px 16px rgba(60,40,120,0.08)", transform: selected === val ? "scale(0.97)" : "scale(1)",
                        transition: "all 0.2s ease" }
                }, val);
            })
        )
    );
}

Object.assign(window, { ActivityScreen, COLORS });

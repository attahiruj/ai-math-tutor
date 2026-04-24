// ReportScreen.js - Parent report view
function ReportScreen({ lang, learner, onBack, api }) {
    const [report, setReport] = React.useState(null);
    const t = window.LANGS[lang];
    const [animIn, setAnimIn] = React.useState(false);

    React.useEffect(() => {
        const fetchReport = async () => {
            try {
                const data = await api.getReport(learner.student_id);
                setReport(data);
                setAnimIn(true);
            } catch (err) {
                console.error("Failed to fetch report:", err);
                setAnimIn(true);
            }
        };
        if (learner?.student_id) fetchReport();
        else setTimeout(() => setAnimIn(true), 50);
    }, [learner]);

    const sessions = report?.attendance_7d || [0, 0, 0, 0, 0, 0, 0];
    const DAY_LABELS = {
        EN: ["M", "T", "W", "T", "F", "S", "S"],
        FR: ["L", "M", "M", "J", "V", "S", "D"],
        KIN: ["Mb", "Ku", "Ka", "Ga", "Ka", "Ka", "Ka"],
    };
    const days = DAY_LABELS[lang] || DAY_LABELS.EN;

    return React.createElement('div', {
        className: "screen", style: { background: "#F4F1FF", overflowY: "auto", justifyContent: "flex-start", paddingTop: 28 },
        'data-screen-label': "05 Parent Report"
    },
        React.createElement('div', {
            style: { width: "100%", maxWidth: 560, opacity: animIn ? 1 : 0, transform: animIn ? "translateY(0)" : "translateY(20px)",
                transition: "all 0.4s ease", display: "flex", flexDirection: "column", gap: 18 }
        },
            // Header card
            React.createElement('div', { className: "card", style: { background: learner?.color || "oklch(68% 0.14 248)", padding: "24px 28px" } },
                React.createElement('div', { style: { display: "flex", alignItems: "center", gap: 16, marginBottom: 12 } },
                    React.createElement('div', {
                        style: { width: 56, height: 56, borderRadius: "50%", background: "rgba(255,255,255,0.3)",
                            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 26, fontWeight: 900, color: "#fff" }
                    }, learner?.avatar || "A"),
                    React.createElement('div', {},
                        React.createElement('div', { style: { fontSize: 22, fontWeight: 900, color: "#fff" } }, learner?.name || "Amara"),
                        React.createElement('div', { style: { fontSize: 15, color: "rgba(255,255,255,0.75)", fontWeight: 600 } }, t.parentTitle)
                    )
                ),
                React.createElement('div', { style: { display: "flex", gap: 20 } },
                    [{ icon: "⭐", val: `${report?.total_stars || 0}`, label: "Stars" },
                     { icon: "📅", val: `${sessions.filter(x => x).length}`, label: "Days" },
                     { icon: "📈", val: `${report?.overall_status || "New"}`, label: "Status" }]
                    .map(item =>
                        React.createElement('div', { key: item.label, style: { flex: 1, background: "rgba(255,255,255,0.2)", borderRadius: 14, padding: "12px 8px", textAlign: "center" } },
                            React.createElement('div', { style: { fontSize: 22 } }, item.icon),
                            React.createElement('div', { style: { fontSize: 20, fontWeight: 900, color: "#fff" } }, item.val),
                            React.createElement('div', { style: { fontSize: 12, color: "rgba(255,255,255,0.75)", fontWeight: 600 } }, item.label)
                        )
                    )
                )
            ),
            // Weekly attendance
            React.createElement('div', { className: "card" },
                React.createElement('div', { style: { fontSize: 17, fontWeight: 800, color: "#1E1A33", marginBottom: 16 } }, `📅 ${t.parentSub}`),
                React.createElement('div', { style: { display: "flex", gap: 10, justifyContent: "space-between" } },
                    sessions.map((active, i) =>
                        React.createElement('div', { key: i, style: { flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 6 } },
                            React.createElement('div', {
                                style: { width: "100%", aspectRatio: "1", borderRadius: 12, background: active ? "oklch(72% 0.14 152)" : "#EDEAF8",
                                    display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }
                            }, active ? "✓" : ""),
                            React.createElement('div', { style: { fontSize: 13, color: "#8A85A5", fontWeight: 700 } }, days[i])
                        )
                    )
                )
            ),
            // Skills
            React.createElement('div', { className: "card" },
                React.createElement('div', { style: { fontSize: 17, fontWeight: 800, color: "#1E1A33", marginBottom: 18 } }, `📊 ${t.skills}`),
                report ? Object.entries(report.skills || {}).map(([key, data]) =>
                    React.createElement(window.ProgressBar, {
                        key, label: t[key] || key, value: animIn ? data.mastery : 0,
                        color: data.mastery > 0.7 ? "oklch(72% 0.14 152)" : data.mastery > 0.4 ? "oklch(84% 0.14 88)" : "oklch(72% 0.14 30)"
                    })
                ) : React.createElement('div', { style: { color: "#8A85A5" } }, "Loading skills...")
            ),
            React.createElement('button', { className: "btn-secondary", onClick: onBack, style: { alignSelf: "center", marginBottom: 12 } }, "← Back")
        )
    );
}

Object.assign(window, { ReportScreen });

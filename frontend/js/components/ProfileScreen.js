// ProfileScreen.js - Learner selection
function ProfileScreen({ lang, onSelect, api }) {
    const t = window.LANGS[lang];
    const [profiles, setProfiles] = React.useState([]);
    const [hovered, setHovered] = React.useState(null);

    React.useEffect(() => {
        // Load profiles from localStorage or use defaults
        const saved = localStorage.getItem('mathkids_profiles');
        if (saved) {
            setProfiles(JSON.parse(saved));
        } else {
            const defaultProfiles = [
                { id: 1, name: "Amara", color: "oklch(68% 0.14 248)", avatar: "A", stars: 14, level: 2 },
                { id: 2, name: "Kofi", color: "oklch(72% 0.14 152)", avatar: "K", stars: 8, level: 1 },
                { id: 3, name: "Safi", color: "oklch(72% 0.14 30)", avatar: "S", stars: 22, level: 3 },
            ];
            setProfiles(defaultProfiles);
            localStorage.setItem('mathkids_profiles', JSON.stringify(defaultProfiles));
        }
    }, []);

    const handleSelect = async (profile) => {
        try {
            const result = await api.startSession(profile.name, lang, profile.avatar);
            onSelect({ ...profile, ...result });
        } catch (err) {
            console.error("Failed to start session:", err);
        }
    };

    return React.createElement('div', {
        className: "screen",
        style: { background: "#F4F1FF", gap: 0 },
        'data-screen-label': "02 Profile Select"
    },
        React.createElement('div', {
            style: { fontSize: 28, fontWeight: 800, color: "#1E1A33", marginBottom: 8, textAlign: "center" }
        }, t.choose),
        React.createElement('div', {
            style: { fontSize: 16, color: "#8A85A5", fontWeight: 600, marginBottom: 40 }
        }, "EN · FR · KIN"),
        React.createElement('div', {
            style: { display: "flex", gap: 24, flexWrap: "wrap", justifyContent: "center" }
        }, profiles.map(p =>
            React.createElement('div', {
                key: p.id,
                onClick: () => handleSelect(p),
                onMouseEnter: () => setHovered(p.id),
                onMouseLeave: () => setHovered(null),
                style: {
                    width: 180, padding: "32px 20px", borderRadius: 24, background: "#fff",
                    boxShadow: hovered === p.id ? "0 12px 40px rgba(60,40,120,0.18)" : "0 4px 20px rgba(60,40,120,0.10)",
                    display: "flex", flexDirection: "column", alignItems: "center", gap: 14, cursor: "pointer",
                    transform: hovered === p.id ? "translateY(-6px)" : "translateY(0)",
                    transition: "all 0.2s ease",
                    border: "3px solid transparent",
                    borderColor: hovered === p.id ? p.color : "transparent",
                }
            },
                React.createElement('div', {
                    style: { width: 80, height: 80, borderRadius: "50%", background: p.color,
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontSize: 34, fontWeight: 900, color: "#fff",
                        boxShadow: `0 4px 16px ${p.color}55` }
                }, p.avatar),
                React.createElement('div', { style: { fontSize: 22, fontWeight: 800, color: "#1E1A33" } }, p.name),
                React.createElement('div', { style: { display: "flex", gap: 4 } },
                    Array.from({ length: 5 }).map((_, i) =>
                        React.createElement('svg', { key: i, width: 18, height: 18, viewBox: "0 0 54 54" },
                            React.createElement('polygon', {
                                points: "27,4 33,20 51,20 37,31 42,48 27,38 12,48 17,31 3,20 21,20",
                                fill: i < Math.min(p.stars / 5, 5) ? "oklch(84% 0.18 88)" : "#E5E0F5"
                            })
                        )
                    )
                ),
                React.createElement('div', { style: { fontSize: 13, color: "#8A85A5", fontWeight: 700 } }, `Level ${p.level}`)
            )
        )),
        React.createElement('button', {
            className: "btn-secondary",
            style: { marginTop: 40 },
            onClick: () => onSelect(null)
        }, "+ Add learner")
    );
}

Object.assign(window, { ProfileScreen });

import { useState, useEffect } from "react";

// ============================================================
// DRIVE Rechteverwaltung — Redesign Mockup
// Umsetzungsvorschlag: "Option B clean" — Portal steuert alles
// ============================================================

const ROLES = [
  { id: "admin", label: "Administrator", color: "#dc2626", icon: "🛡️", desc: "Voller Zugriff auf alle Module und Verwaltung" },
  { id: "geschaeftsfuehrung", label: "Geschäftsführung", color: "#7c3aed", icon: "👔", desc: "Alle Module, Reports, Finanzdaten" },
  { id: "buchhaltung", label: "Buchhaltung", color: "#2563eb", icon: "📊", desc: "Bankenspiegel, Controlling, OPOS, BWA" },
  { id: "verkauf", label: "Verkauf", color: "#059669", icon: "🚗", desc: "Auftragseingang, Auslieferungen, Provision" },
  { id: "verkauf_leitung", label: "Verkaufsleitung", color: "#0d9488", icon: "📈", desc: "Verkauf + Team-Reports + Margen" },
  { id: "werkstatt", label: "Werkstatt/Service", color: "#d97706", icon: "🔧", desc: "Werkstatt-Dashboard, Zeiterfassung" },
  { id: "service_leitung", label: "Serviceleitung", color: "#ea580c", icon: "⚙️", desc: "Werkstatt + Team-Reports + Auslastung" },
  { id: "teile", label: "Teile & Zubehör", color: "#6366f1", icon: "📦", desc: "Teile-Bestand, Bestellungen" },
  { id: "mitarbeiter", label: "Mitarbeiter", color: "#6b7280", icon: "👤", desc: "Minimaler Zugriff: Urlaub, eigene Daten" },
];

const FEATURES = [
  { id: "bankenspiegel", label: "Bankenspiegel", group: "Finanzen", icon: "🏦" },
  { id: "controlling", label: "Controlling / BWA", group: "Finanzen", icon: "📊" },
  { id: "opos", label: "OPOS", group: "Finanzen", icon: "📋" },
  { id: "einkaufsfinanzierung", label: "Einkaufsfinanzierung", group: "Finanzen", icon: "💳" },
  { id: "fahrzeugfinanzierung", label: "Fahrzeug-Zinsen", group: "Finanzen", icon: "🏷️" },
  { id: "auftragseingang", label: "Auftragseingang", group: "Verkauf", icon: "📝" },
  { id: "auslieferungen", label: "Auslieferungen", group: "Verkauf", icon: "🚚" },
  { id: "provision", label: "Provision / Deckungsbeitrag", group: "Verkauf", icon: "💰" },
  { id: "fahrzeugbestand", label: "Fahrzeugbestand", group: "Verkauf", icon: "🅿️" },
  { id: "werkstatt_dashboard", label: "Werkstatt-Dashboard", group: "Werkstatt", icon: "🔧" },
  { id: "zeiterfassung", label: "Zeiterfassung", group: "Werkstatt", icon: "⏱️" },
  { id: "tek", label: "TEK / Produktivität", group: "Werkstatt", icon: "📈" },
  { id: "urlaubsplaner", label: "Urlaubsplaner", group: "HR", icon: "🏖️" },
  { id: "mitarbeiter_verwaltung", label: "Mitarbeiter", group: "HR", icon: "👥" },
  { id: "whatsapp", label: "WhatsApp", group: "Kommunikation", icon: "💬" },
  { id: "admin_panel", label: "Admin-Panel", group: "System", icon: "⚙️" },
  { id: "rechteverwaltung", label: "Rechteverwaltung", group: "System", icon: "🔐" },
];

const DEFAULT_FEATURE_MAP = {
  admin: FEATURES.map(f => f.id),
  geschaeftsfuehrung: FEATURES.filter(f => f.id !== "rechteverwaltung").map(f => f.id),
  buchhaltung: ["bankenspiegel", "controlling", "opos", "einkaufsfinanzierung", "fahrzeugfinanzierung", "auftragseingang", "auslieferungen", "urlaubsplaner"],
  verkauf: ["auftragseingang", "auslieferungen", "fahrzeugbestand", "urlaubsplaner"],
  verkauf_leitung: ["auftragseingang", "auslieferungen", "fahrzeugbestand", "provision", "urlaubsplaner", "mitarbeiter_verwaltung"],
  werkstatt: ["werkstatt_dashboard", "zeiterfassung", "urlaubsplaner"],
  service_leitung: ["werkstatt_dashboard", "zeiterfassung", "tek", "urlaubsplaner", "mitarbeiter_verwaltung"],
  teile: ["fahrzeugbestand", "urlaubsplaner"],
  mitarbeiter: ["urlaubsplaner"],
};

const MOCK_USERS = [
  { id: 1, name: "Florian Greiner", username: "florian.greiner@auto-greiner.de", ou: "Geschäftsleitung", title: "Geschäftsführer", portal_role: "admin", override: "admin", lastLogin: "19.02.2026 08:12", standort: "Deggendorf" },
  { id: 2, name: "Silvia Eiglmaier", username: "silvia.eiglmaier@auto-greiner.de", ou: "Buchhaltung", title: "Mitarbeiterin Buchhaltung", portal_role: "verkauf", override: "verkauf", lastLogin: "19.02.2026 09:45", standort: "Deggendorf", highlight: true },
  { id: 3, name: "Anton Süß", username: "anton.suess@auto-greiner.de", ou: "Verkauf", title: "Verkaufsleiter", portal_role: "verkauf_leitung", override: "verkauf_leitung", lastLogin: "18.02.2026 17:30", standort: "Deggendorf" },
  { id: 4, name: "Christian Meier", username: "christian.meier@auto-greiner.de", ou: "Service", title: "Serviceberater", portal_role: "werkstatt", override: null, lastLogin: "19.02.2026 07:55", standort: "Deggendorf" },
  { id: 5, name: "Vanessa Huber", username: "vanessa.huber@auto-greiner.de", ou: "Geschäftsleitung", title: "Assistentin GL", portal_role: "geschaeftsfuehrung", override: "geschaeftsfuehrung", lastLogin: "19.02.2026 08:30", standort: "Deggendorf" },
  { id: 6, name: "Max Berger", username: "max.berger@auto-greiner.de", ou: "Werkstatt", title: "Monteur", portal_role: "mitarbeiter", override: null, lastLogin: "18.02.2026 16:00", standort: "Landau" },
  { id: 7, name: "Lisa Bauer", username: "lisa.bauer@auto-greiner.de", ou: "Verkauf", title: "Verkäuferin", portal_role: null, override: null, lastLogin: "17.02.2026 14:20", standort: "Landau", noRole: true },
  { id: 8, name: "Thomas Wagner", username: "thomas.wagner@auto-greiner.de", ou: "Teile und Zubehör", title: "Teiledienstleiter", portal_role: "teile", override: "teile", lastLogin: "19.02.2026 09:10", standort: "Deggendorf" },
];

// Grouped features for display
function groupFeatures(features) {
  const groups = {};
  features.forEach(f => {
    if (!groups[f.group]) groups[f.group] = [];
    groups[f.group].push(f);
  });
  return groups;
}

// ============ COMPONENTS ============

function RoleBadge({ roleId, small }) {
  const role = ROLES.find(r => r.id === roleId);
  if (!role) return <span style={{ fontSize: small ? 11 : 12, color: "#9ca3af", background: "#f3f4f6", padding: "2px 8px", borderRadius: 4 }}>— nicht zugewiesen —</span>;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      fontSize: small ? 11 : 12, fontWeight: 600,
      color: role.color, background: role.color + "12",
      border: `1px solid ${role.color}30`,
      padding: small ? "1px 6px" : "2px 10px", borderRadius: 6,
      whiteSpace: "nowrap"
    }}>
      {role.icon} {role.label}
    </span>
  );
}

function SourceIndicator({ override }) {
  if (override) {
    return <span style={{ fontSize: 10, color: "#059669", fontWeight: 600, background: "#ecfdf5", padding: "1px 6px", borderRadius: 4 }}>Portal ✓</span>;
  }
  return <span style={{ fontSize: 10, color: "#6b7280", background: "#f9fafb", padding: "1px 6px", borderRadius: 4 }}>Default</span>;
}

// ============ TABS ============

function UserTab({ users, setUsers, selectedUser, setSelectedUser, setActiveTab }) {
  const [search, setSearch] = useState("");
  const [filterStandort, setFilterStandort] = useState("alle");
  const [filterStatus, setFilterStatus] = useState("alle");
  const [editingUser, setEditingUser] = useState(null);
  const [tempRole, setTempRole] = useState("");
  const [showSuccess, setShowSuccess] = useState(null);

  const filtered = users.filter(u => {
    if (search && !u.name.toLowerCase().includes(search.toLowerCase()) && !u.username.toLowerCase().includes(search.toLowerCase())) return false;
    if (filterStandort !== "alle" && u.standort !== filterStandort) return false;
    if (filterStatus === "ohne_rolle" && u.portal_role) return false;
    if (filterStatus === "mit_override" && !u.override) return false;
    if (filterStatus === "ohne_override" && u.override) return false;
    return true;
  });

  const handleSaveRole = (userId) => {
    setUsers(prev => prev.map(u => {
      if (u.id === userId) {
        const newRole = tempRole || null;
        return { ...u, portal_role: newRole || "mitarbeiter", override: newRole, noRole: !newRole, highlight: false };
      }
      return u;
    }));
    setShowSuccess(userId);
    setTimeout(() => setShowSuccess(null), 2000);
    setEditingUser(null);
  };

  return (
    <div>
      {/* Info Banner */}
      <div style={{ background: "linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%)", border: "1px solid #bfdbfe", borderRadius: 10, padding: "14px 18px", marginBottom: 20, display: "flex", gap: 12, alignItems: "flex-start" }}>
        <span style={{ fontSize: 20 }}>💡</span>
        <div style={{ fontSize: 13, color: "#1e40af", lineHeight: 1.5 }}>
          <strong>So funktioniert's:</strong> Jeder User bekommt <strong>eine Portal-Rolle</strong> zugewiesen. Diese bestimmt, welche Navi-Punkte und Features sichtbar sind.
          LDAP liefert nur die Identität (Login). Ohne zugewiesene Rolle → Default "Mitarbeiter" (minimaler Zugriff).
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap" }}>
        <input
          value={search} onChange={e => setSearch(e.target.value)}
          placeholder="🔍  Name oder E-Mail suchen…"
          style={{ flex: 1, minWidth: 200, padding: "8px 14px", border: "1px solid #d1d5db", borderRadius: 8, fontSize: 13, outline: "none" }}
        />
        <select value={filterStandort} onChange={e => setFilterStandort(e.target.value)}
          style={{ padding: "8px 12px", border: "1px solid #d1d5db", borderRadius: 8, fontSize: 13, background: "white" }}>
          <option value="alle">Alle Standorte</option>
          <option value="Deggendorf">Deggendorf</option>
          <option value="Landau">Landau</option>
        </select>
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
          style={{ padding: "8px 12px", border: "1px solid #d1d5db", borderRadius: 8, fontSize: 13, background: "white" }}>
          <option value="alle">Alle User</option>
          <option value="ohne_rolle">⚠ Ohne Rolle</option>
          <option value="mit_override">✅ Mit Portal-Rolle</option>
          <option value="ohne_override">📋 Nur Default</option>
        </select>
      </div>

      {/* Counter */}
      <div style={{ fontSize: 12, color: "#6b7280", marginBottom: 10 }}>
        {filtered.length} von {users.length} Benutzer{users.length !== 1 ? "n" : ""}
        {users.filter(u => u.noRole).length > 0 && (
          <span style={{ color: "#dc2626", fontWeight: 600, marginLeft: 12 }}>
            ⚠ {users.filter(u => u.noRole).length} ohne Rolle
          </span>
        )}
      </div>

      {/* User Table */}
      <div style={{ borderRadius: 10, border: "1px solid #e5e7eb", overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: "#f8fafc" }}>
              <th style={{ padding: "10px 14px", textAlign: "left", fontWeight: 600, color: "#374151", borderBottom: "2px solid #e5e7eb" }}>Mitarbeiter</th>
              <th style={{ padding: "10px 14px", textAlign: "left", fontWeight: 600, color: "#374151", borderBottom: "2px solid #e5e7eb" }}>LDAP-Info</th>
              <th style={{ padding: "10px 14px", textAlign: "left", fontWeight: 600, color: "#374151", borderBottom: "2px solid #e5e7eb" }}>Portal-Rolle</th>
              <th style={{ padding: "10px 14px", textAlign: "left", fontWeight: 600, color: "#374151", borderBottom: "2px solid #e5e7eb" }}>Quelle</th>
              <th style={{ padding: "10px 14px", textAlign: "center", fontWeight: 600, color: "#374151", borderBottom: "2px solid #e5e7eb", width: 120 }}>Aktion</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((user, i) => (
              <tr key={user.id} style={{
                borderBottom: "1px solid #f3f4f6",
                background: user.noRole ? "#fef2f210" : user.highlight ? "#fefce810" : (selectedUser === user.id ? "#eff6ff" : (i % 2 === 0 ? "white" : "#fafafa")),
                transition: "background 0.15s"
              }}
                onMouseEnter={e => { if (selectedUser !== user.id) e.currentTarget.style.background = "#f0f9ff" }}
                onMouseLeave={e => { if (selectedUser !== user.id) e.currentTarget.style.background = user.noRole ? "#fef2f210" : (i % 2 === 0 ? "white" : "#fafafa") }}
              >
                <td style={{ padding: "10px 14px" }}>
                  <div style={{ fontWeight: 600, color: "#111827" }}>
                    {user.noRole && <span style={{ color: "#dc2626", marginRight: 4 }}>⚠</span>}
                    {user.highlight && <span style={{ color: "#eab308", marginRight: 4 }}>★</span>}
                    {user.name}
                  </div>
                  <div style={{ fontSize: 11, color: "#6b7280" }}>{user.standort} · {user.lastLogin}</div>
                </td>
                <td style={{ padding: "10px 14px" }}>
                  <div style={{ fontSize: 11, color: "#9ca3af" }}>
                    OU: <span style={{ color: "#6b7280" }}>{user.ou}</span>
                  </div>
                  <div style={{ fontSize: 11, color: "#9ca3af" }}>
                    Titel: <span style={{ color: "#6b7280" }}>{user.title}</span>
                  </div>
                </td>
                <td style={{ padding: "10px 14px" }}>
                  {editingUser === user.id ? (
                    <select
                      value={tempRole}
                      onChange={e => setTempRole(e.target.value)}
                      style={{ padding: "4px 8px", border: "2px solid #3b82f6", borderRadius: 6, fontSize: 12, background: "#eff6ff", outline: "none" }}
                      autoFocus
                    >
                      <option value="">— Bitte zuweisen —</option>
                      {ROLES.map(r => (
                        <option key={r.id} value={r.id}>{r.icon} {r.label}</option>
                      ))}
                    </select>
                  ) : (
                    <RoleBadge roleId={user.portal_role} />
                  )}
                </td>
                <td style={{ padding: "10px 14px" }}>
                  <SourceIndicator override={user.override} />
                </td>
                <td style={{ padding: "10px 14px", textAlign: "center" }}>
                  {showSuccess === user.id ? (
                    <span style={{ color: "#059669", fontSize: 12, fontWeight: 600 }}>✓ Gespeichert!</span>
                  ) : editingUser === user.id ? (
                    <div style={{ display: "flex", gap: 4, justifyContent: "center" }}>
                      <button onClick={() => handleSaveRole(user.id)}
                        style={{ padding: "4px 10px", background: "#059669", color: "white", border: "none", borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: "pointer" }}>
                        Speichern
                      </button>
                      <button onClick={() => setEditingUser(null)}
                        style={{ padding: "4px 8px", background: "#f3f4f6", color: "#6b7280", border: "1px solid #d1d5db", borderRadius: 6, fontSize: 11, cursor: "pointer" }}>
                        ✕
                      </button>
                    </div>
                  ) : (
                    <button onClick={() => { setEditingUser(user.id); setTempRole(user.override || user.portal_role || ""); }}
                      style={{ padding: "4px 12px", background: "white", color: "#3b82f6", border: "1px solid #bfdbfe", borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: "pointer" }}>
                      Rolle ändern
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RoleFeatureTab() {
  const [selectedRole, setSelectedRole] = useState("buchhaltung");
  const [featureMap, setFeatureMap] = useState(DEFAULT_FEATURE_MAP);
  const [showSaved, setShowSaved] = useState(false);
  const grouped = groupFeatures(FEATURES);
  const role = ROLES.find(r => r.id === selectedRole);
  const enabledFeatures = featureMap[selectedRole] || [];

  const toggleFeature = (featureId) => {
    setFeatureMap(prev => {
      const current = prev[selectedRole] || [];
      if (current.includes(featureId)) {
        return { ...prev, [selectedRole]: current.filter(f => f !== featureId) };
      } else {
        return { ...prev, [selectedRole]: [...current, featureId] };
      }
    });
  };

  const handleSave = () => {
    setShowSaved(true);
    setTimeout(() => setShowSaved(false), 2000);
  };

  return (
    <div>
      <div style={{ background: "linear-gradient(135deg, #faf5ff 0%, #fdf2f8 100%)", border: "1px solid #e9d5ff", borderRadius: 10, padding: "14px 18px", marginBottom: 20, fontSize: 13, color: "#6b21a8", lineHeight: 1.5 }}>
        <strong>💡 Rollen-Features:</strong> Hier legst du fest, welche Module jede Rolle sehen darf. Änderungen gelten für <strong>alle User</strong> mit dieser Rolle.
      </div>

      {/* Role Selector */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 20 }}>
        {ROLES.map(r => (
          <button
            key={r.id}
            onClick={() => setSelectedRole(r.id)}
            style={{
              padding: "8px 14px", borderRadius: 8, fontSize: 12, fontWeight: 600,
              cursor: "pointer", transition: "all 0.15s",
              border: selectedRole === r.id ? `2px solid ${r.color}` : "1px solid #e5e7eb",
              background: selectedRole === r.id ? r.color + "10" : "white",
              color: selectedRole === r.id ? r.color : "#6b7280",
            }}
          >
            {r.icon} {r.label}
            <span style={{ marginLeft: 6, fontSize: 10, opacity: 0.7 }}>
              ({(featureMap[r.id] || []).length})
            </span>
          </button>
        ))}
      </div>

      {/* Selected Role Info */}
      {role && (
        <div style={{
          background: `linear-gradient(135deg, ${role.color}08 0%, ${role.color}04 100%)`,
          border: `1px solid ${role.color}20`,
          borderRadius: 10, padding: "12px 18px", marginBottom: 20,
          display: "flex", justifyContent: "space-between", alignItems: "center"
        }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: role.color }}>{role.icon} {role.label}</div>
            <div style={{ fontSize: 12, color: "#6b7280", marginTop: 2 }}>{role.desc}</div>
          </div>
          <div style={{ fontSize: 12, color: "#6b7280" }}>
            <strong style={{ fontSize: 20, color: role.color }}>{enabledFeatures.length}</strong> / {FEATURES.length} Features
          </div>
        </div>
      )}

      {/* Feature Groups */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {Object.entries(grouped).map(([group, features]) => (
          <div key={group} style={{ border: "1px solid #e5e7eb", borderRadius: 10, overflow: "hidden" }}>
            <div style={{ background: "#f8fafc", padding: "8px 14px", fontWeight: 700, fontSize: 12, color: "#374151", borderBottom: "1px solid #e5e7eb", display: "flex", justifyContent: "space-between" }}>
              <span>{group}</span>
              <span style={{ fontSize: 10, color: "#9ca3af" }}>
                {features.filter(f => enabledFeatures.includes(f.id)).length}/{features.length}
              </span>
            </div>
            <div style={{ padding: 8 }}>
              {features.map(feature => {
                const enabled = enabledFeatures.includes(feature.id);
                return (
                  <label
                    key={feature.id}
                    style={{
                      display: "flex", alignItems: "center", gap: 10, padding: "6px 8px",
                      borderRadius: 6, cursor: selectedRole === "admin" ? "not-allowed" : "pointer",
                      background: enabled ? "#f0fdf4" : "transparent",
                      opacity: selectedRole === "admin" ? 0.6 : 1,
                      transition: "background 0.15s"
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={enabled}
                      onChange={() => toggleFeature(feature.id)}
                      disabled={selectedRole === "admin"}
                      style={{ accentColor: role?.color || "#3b82f6", width: 16, height: 16 }}
                    />
                    <span style={{ fontSize: 14 }}>{feature.icon}</span>
                    <span style={{ fontSize: 12, fontWeight: enabled ? 600 : 400, color: enabled ? "#111827" : "#6b7280" }}>
                      {feature.label}
                    </span>
                  </label>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Save Button */}
      <div style={{ marginTop: 20, display: "flex", justifyContent: "flex-end", gap: 10 }}>
        {showSaved && <span style={{ color: "#059669", fontSize: 13, fontWeight: 600, alignSelf: "center" }}>✓ Gespeichert!</span>}
        <button onClick={handleSave}
          style={{
            padding: "10px 24px", background: role?.color || "#3b82f6", color: "white",
            border: "none", borderRadius: 8, fontSize: 13, fontWeight: 700,
            cursor: "pointer", boxShadow: "0 2px 8px rgba(0,0,0,0.15)"
          }}>
          Änderungen speichern
        </button>
      </div>
    </div>
  );
}

function MatrixTab() {
  const [featureMap] = useState(DEFAULT_FEATURE_MAP);
  return (
    <div>
      <div style={{ background: "linear-gradient(135deg, #fefce8 0%, #fef9c3 100%)", border: "1px solid #fde68a", borderRadius: 10, padding: "14px 18px", marginBottom: 20, fontSize: 13, color: "#92400e", lineHeight: 1.5 }}>
        <strong>📋 Berechtigungsmatrix:</strong> Gesamtübersicht — welche Rolle hat Zugriff auf welches Feature. Read-only.
      </div>

      <div style={{ borderRadius: 10, border: "1px solid #e5e7eb", overflow: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
          <thead>
            <tr style={{ background: "#f8fafc" }}>
              <th style={{ padding: "8px 12px", textAlign: "left", fontWeight: 700, color: "#374151", borderBottom: "2px solid #e5e7eb", position: "sticky", left: 0, background: "#f8fafc", minWidth: 160 }}>Feature</th>
              {ROLES.map(r => (
                <th key={r.id} style={{
                  padding: "6px 4px", textAlign: "center", fontWeight: 600,
                  color: r.color, borderBottom: "2px solid #e5e7eb",
                  fontSize: 10, minWidth: 70, whiteSpace: "nowrap"
                }}>
                  <div>{r.icon}</div>
                  <div>{r.label.split("/")[0]}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Object.entries(groupFeatures(FEATURES)).map(([group, features]) => (
              <>
                <tr key={`group-${group}`}>
                  <td colSpan={ROLES.length + 1} style={{ padding: "6px 12px", fontWeight: 700, fontSize: 10, color: "#6b7280", background: "#f9fafb", textTransform: "uppercase", letterSpacing: 0.5, borderBottom: "1px solid #e5e7eb" }}>
                    {group}
                  </td>
                </tr>
                {features.map(feature => (
                  <tr key={feature.id} style={{ borderBottom: "1px solid #f3f4f6" }}>
                    <td style={{ padding: "6px 12px", fontWeight: 500, color: "#374151", position: "sticky", left: 0, background: "white" }}>
                      {feature.icon} {feature.label}
                    </td>
                    {ROLES.map(r => {
                      const has = (featureMap[r.id] || []).includes(feature.id);
                      return (
                        <td key={r.id} style={{ padding: "4px", textAlign: "center" }}>
                          {has ? (
                            <span style={{ color: "#059669", fontSize: 16, fontWeight: 700 }}>✓</span>
                          ) : (
                            <span style={{ color: "#e5e7eb", fontSize: 14 }}>—</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ArchitectureTab() {
  return (
    <div>
      <div style={{ background: "linear-gradient(135deg, #f0fdfa 0%, #ecfdf5 100%)", border: "1px solid #99f6e4", borderRadius: 10, padding: "14px 18px", marginBottom: 20, fontSize: 13, color: "#115e59", lineHeight: 1.5 }}>
        <strong>🏗️ Architektur-Übersicht:</strong> So wird die Portal-Rolle ermittelt — eine klare Kaskade, kein Doppeldeutig.
      </div>

      {/* Decision Cascade */}
      <div style={{ display: "flex", flexDirection: "column", gap: 0, alignItems: "center", maxWidth: 520, margin: "0 auto 30px" }}>
        {[
          { step: 1, label: "Login via LDAP", desc: "AD liefert nur: ✓ Identität (wer bist du?) — KEINE Rechte!", color: "#6366f1", icon: "🔑" },
          { step: 2, label: "admin in user_roles?", desc: "Ja → Rolle = admin, voller Zugriff. Fertig.", color: "#dc2626", icon: "🛡️", highlight: true },
          { step: 3, label: "portal_role_override gesetzt?", desc: "Ja → Diese Rolle verwenden (vom Admin im Portal zugewiesen)", color: "#059669", icon: "✅", highlight: true },
          { step: 4, label: "Fallback: mitarbeiter", desc: "Minimaler Zugriff (nur Urlaubsplaner, eigene Daten)", color: "#6b7280", icon: "👤" },
        ].map((item, i) => (
          <div key={i} style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center" }}>
            {i > 0 && (
              <div style={{ width: 2, height: 20, background: "#d1d5db" }} />
            )}
            <div style={{
              width: "100%", padding: "14px 18px", borderRadius: 10,
              background: item.highlight ? `${item.color}08` : "white",
              border: `2px solid ${item.color}${item.highlight ? "40" : "20"}`,
              display: "flex", gap: 14, alignItems: "center"
            }}>
              <div style={{
                width: 36, height: 36, borderRadius: "50%",
                background: item.color, color: "white",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 14, fontWeight: 800, flexShrink: 0
              }}>
                {item.step}
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 14, color: item.color }}>
                  {item.icon} {item.label}
                </div>
                <div style={{ fontSize: 12, color: "#6b7280", marginTop: 2 }}>{item.desc}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Code Changes Summary */}
      <div style={{ background: "#1e293b", borderRadius: 10, padding: 20, color: "#e2e8f0", fontFamily: "monospace", fontSize: 12, lineHeight: 1.7 }}>
        <div style={{ color: "#94a3b8", marginBottom: 8 }}># Betroffene Dateien — Änderungen</div>
        <div style={{ color: "#fbbf24" }}>auth/auth_manager.py</div>
        <div style={{ color: "#86efac", paddingLeft: 16 }}>+ get_user_by_id(): portal_role_override prüfen</div>
        <div style={{ color: "#86efac", paddingLeft: 16 }}>+ authenticate_user(): override NICHT überschreiben</div>
        <div style={{ color: "#fca5a5", paddingLeft: 16 }}>- LDAP title → portal_role Ableitung entfernen</div>
        <div style={{ height: 8 }} />
        <div style={{ color: "#fbbf24" }}>api/admin_api.py</div>
        <div style={{ color: "#86efac", paddingLeft: 16 }}>+ POST /admin/user/&lt;id&gt;/portal-role</div>
        <div style={{ color: "#86efac", paddingLeft: 16 }}>+ GET/PUT /admin/role/&lt;name&gt;/features</div>
        <div style={{ height: 8 }} />
        <div style={{ color: "#fbbf24" }}>config/roles_config.py</div>
        <div style={{ color: "#86efac", paddingLeft: 16 }}>+ ROLES dict (ersetzt verteilte Configs)</div>
        <div style={{ color: "#fca5a5", paddingLeft: 16 }}>- get_role_from_title() entfernen</div>
        <div style={{ color: "#fca5a5", paddingLeft: 16 }}>- TITLE_TO_ROLE Mapping entfernen</div>
        <div style={{ height: 8 }} />
        <div style={{ color: "#fbbf24" }}>DB: users Tabelle</div>
        <div style={{ color: "#86efac", paddingLeft: 16 }}>+ ALTER TABLE users ADD COLUMN portal_role_override TEXT</div>
        <div style={{ height: 8 }} />
        <div style={{ color: "#fbbf24" }}>DB: feature_access Tabelle</div>
        <div style={{ color: "#94a3b8", paddingLeft: 16 }}>  Bestehend — wird SSOT (kein Config-Fallback mehr)</div>
      </div>

      {/* Migration Note */}
      <div style={{ marginTop: 20, background: "#fefce8", border: "1px solid #fde68a", borderRadius: 10, padding: "14px 18px", fontSize: 13, color: "#92400e" }}>
        <strong>⚡ Migration:</strong> Einmalig alle bestehenden User durchgehen und portal_role_override setzen basierend auf aktuellem title→role Mapping. Danach ist TITLE_TO_ROLE obsolet.
        Ein Script <code>scripts/migrations/migrate_to_portal_role_override.py</code> erledigt das.
      </div>
    </div>
  );
}

// ============ MAIN APP ============

export default function RechteverwaltungMockup() {
  const [activeTab, setActiveTab] = useState("users");
  const [users, setUsers] = useState(MOCK_USERS);
  const [selectedUser, setSelectedUser] = useState(null);

  const tabs = [
    { id: "users", label: "User & Rollen", icon: "👥", count: users.length },
    { id: "features", label: "Rollen-Features", icon: "🎛️" },
    { id: "matrix", label: "Matrix", icon: "📋" },
    { id: "architektur", label: "Architektur", icon: "🏗️" },
  ];

  return (
    <div style={{ fontFamily: "'Segoe UI', -apple-system, sans-serif", background: "#f8fafc", minHeight: "100vh" }}>
      {/* Header */}
      <div style={{
        background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
        padding: "20px 28px", color: "white"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 1.5, color: "#94a3b8", marginBottom: 4 }}>
              DRIVE · Admin
            </div>
            <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: -0.5 }}>
              🔐 Rechteverwaltung
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 12, color: "#94a3b8" }}>Angemeldet als</div>
            <div style={{ fontSize: 14, fontWeight: 600 }}>Florian Greiner</div>
            <RoleBadge roleId="admin" small />
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <div style={{ background: "white", borderBottom: "1px solid #e5e7eb", padding: "10px 28px", display: "flex", gap: 24, fontSize: 12 }}>
        <span style={{ color: "#059669" }}>✓ <strong>{users.filter(u => u.override).length}</strong> mit Portal-Rolle</span>
        <span style={{ color: "#6b7280" }}>📋 <strong>{users.filter(u => !u.override && !u.noRole).length}</strong> Default</span>
        <span style={{ color: "#dc2626" }}>⚠ <strong>{users.filter(u => u.noRole).length}</strong> ohne Rolle</span>
        <span style={{ color: "#6366f1", marginLeft: "auto" }}>SSOT: Portal (Option B)</span>
      </div>

      {/* Tabs */}
      <div style={{ background: "white", borderBottom: "1px solid #e5e7eb", padding: "0 28px", display: "flex", gap: 0 }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: "12px 20px", border: "none", cursor: "pointer",
              fontSize: 13, fontWeight: activeTab === tab.id ? 700 : 500,
              color: activeTab === tab.id ? "#1e40af" : "#6b7280",
              background: "transparent",
              borderBottom: activeTab === tab.id ? "3px solid #3b82f6" : "3px solid transparent",
              transition: "all 0.15s"
            }}
          >
            {tab.icon} {tab.label}
            {tab.count && <span style={{ marginLeft: 6, fontSize: 10, background: "#f3f4f6", padding: "1px 6px", borderRadius: 10 }}>{tab.count}</span>}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ padding: "24px 28px", maxWidth: 1100, margin: "0 auto" }}>
        {activeTab === "users" && <UserTab users={users} setUsers={setUsers} selectedUser={selectedUser} setSelectedUser={setSelectedUser} setActiveTab={setActiveTab} />}
        {activeTab === "features" && <RoleFeatureTab />}
        {activeTab === "matrix" && <MatrixTab />}
        {activeTab === "architektur" && <ArchitectureTab />}
      </div>
    </div>
  );
}

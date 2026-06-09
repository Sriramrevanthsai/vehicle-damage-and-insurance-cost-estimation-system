import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_BASE = getApiBase();

const vehicleSegments = [
  { value: "hatchback", label: "Hatchback" },
  { value: "sedan", label: "Sedan" },
  { value: "suv", label: "SUV" },
  { value: "luxury", label: "Luxury" },
];

const carModels = [
  { value: "maruti_swift", label: "Maruti Suzuki Swift" },
  { value: "hyundai_i20", label: "Hyundai i20" },
  { value: "tata_altroz", label: "Tata Altroz" },
  { value: "maruti_baleno", label: "Maruti Suzuki Baleno" },
  { value: "honda_amaze", label: "Honda Amaze" },
  { value: "hyundai_verna", label: "Hyundai Verna" },
  { value: "honda_city", label: "Honda City" },
  { value: "skoda_slavia", label: "Skoda Slavia" },
  { value: "tata_nexon", label: "Tata Nexon" },
  { value: "hyundai_creta", label: "Hyundai Creta" },
  { value: "kia_seltos", label: "Kia Seltos" },
  { value: "mahindra_xuv700", label: "Mahindra XUV700" },
  { value: "toyota_innova", label: "Toyota Innova Crysta" },
  { value: "mg_hector", label: "MG Hector" },
  { value: "jeep_compass", label: "Jeep Compass" },
  { value: "bmw_3_series", label: "BMW 3 Series" },
  { value: "mercedes_c_class", label: "Mercedes-Benz C-Class" },
  { value: "audi_a4", label: "Audi A4" },
];

const damageCategories = [
  { value: "auto", label: "Auto from AI model" },
  { value: "broken_glass", label: "Broken glass" },
  { value: "dent", label: "Dent" },
  { value: "paint_damage", label: "Paint damage" },
  { value: "missing_part", label: "Missing part" },
  { value: "scratch", label: "Scratch" },
  { value: "deformation", label: "Deformation" },
];

const workshopTypes = [
  { value: "independent", label: "Independent" },
  { value: "standard", label: "Standard" },
  { value: "authorized", label: "Authorized" },
];

function App() {
  const [token, setToken] = useState(localStorage.getItem("insurance_token") || "");
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState({ full_name: "", email: "", password: "" });
  const [view, setView] = useState("assess");
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [result, setResult] = useState(null);
  const [claims, setClaims] = useState([]);
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [vehicleSegment, setVehicleSegment] = useState("sedan");
  const [workshopType, setWorkshopType] = useState("standard");
  const [carModel, setCarModel] = useState("maruti_swift");
  const [damageCategory, setDamageCategory] = useState("auto");

  const hasResult = Boolean(result);
  const activeResult = selectedClaim || result;
  const severityClass = useMemo(() => {
    if (!activeResult?.severity) return "";
    return `severity-${activeResult.severity.toLowerCase()}`;
  }, [activeResult]);

  useEffect(() => {
    const storedToken = localStorage.getItem("insurance_token") || "";
    if (!storedToken) return;
    apiFetch("/auth/me", { token: storedToken })
      .then((data) => {
        setToken(storedToken);
        setUser(data.user);
        return apiFetch("/claims", { token: storedToken });
      })
      .then((data) => setClaims(data.claims))
      .catch(() => handleLogout());
  }, []);

  const loadClaims = async (authToken = token) => {
    if (!authToken) return;
    const data = await apiFetch("/claims", { token: authToken });
    setClaims(data.claims);
  };

  const handleAuth = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const path = authMode === "login" ? "/auth/login" : "/auth/register";
      const payload =
        authMode === "login"
          ? { email: authForm.email, password: authForm.password }
          : authForm;
      const data = await apiFetch(path, { method: "POST", body: payload });
      localStorage.setItem("insurance_token", data.token);
      setToken(data.token);
      setUser(data.user);
      setView("assess");
      await loadClaims(data.token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("insurance_token");
    setToken("");
    setUser(null);
    setClaims([]);
    setResult(null);
    setSelectedClaim(null);
    setView("assess");
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    setResult(null);
    setSelectedClaim(null);
    setError("");
    setSelectedFile(file || null);
    setPreview(file ? URL.createObjectURL(file) : "");
  };

  const analyzeImage = async () => {
    if (!selectedFile) {
      setError("Select a vehicle damage image first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("vehicle_segment", vehicleSegment);
    formData.append("workshop_type", workshopType);
    formData.append("car_model", carModel);
    formData.append("damage_category", damageCategory);

    setLoading(true);
    setError("");
    try {
      const data = await apiFetch("/predict", { method: "POST", token, formData });
      setResult(data);
      setSelectedClaim(null);
      await loadClaims();
    } catch (err) {
      setError(err.message || "Failed to process image. Check that the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const openClaim = async (claimId) => {
    setError("");
    setLoading(true);
    try {
      const data = await apiFetch(`/claims/${claimId}`, { token });
      setSelectedClaim(data.claim);
      setResult(null);
      setView("report");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveClaim = async (claimId) => {
    setError("");
    setLoading(true);
    try {
      await apiFetch(`/claims/${claimId}/approve`, { method: "PATCH", token });
      await loadClaims();
      setError("Claim approved successfully!");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const printReport = () => window.print();

  if (!user) {
    return (
      <main className="auth-shell">
        <section className="auth-panel">
          <div className="brand-block">
            <span className="eyebrow">RT-DETR-L Insurance Assist</span>
            <h1>Vehicle Damage Claim Portal</h1>
            <p>Sign in to save claim history, generate reports, and keep AI assessments organized.</p>
          </div>
          <form className="auth-card" onSubmit={handleAuth}>
            <div className="auth-tabs">
              <button type="button" className={authMode === "login" ? "active" : ""} onClick={() => setAuthMode("login")}>
                Login
              </button>
              <button type="button" className={authMode === "register" ? "active" : ""} onClick={() => setAuthMode("register")}>
                Create account
              </button>
            </div>
            {authMode === "register" && (
              <label>
                <span>Full name</span>
                <input value={authForm.full_name} onChange={(event) => setAuthForm({ ...authForm, full_name: event.target.value })} />
              </label>
            )}
            <label>
              <span>Email</span>
              <input type="email" value={authForm.email} onChange={(event) => setAuthForm({ ...authForm, email: event.target.value })} />
            </label>
            <label>
              <span>Password</span>
              <input type="password" value={authForm.password} onChange={(event) => setAuthForm({ ...authForm, password: event.target.value })} />
            </label>
            <button className="primary-action" type="submit" disabled={loading}>
              {loading ? "Please wait..." : authMode === "login" ? "Login" : "Create account"}
            </button>
            {error && <p className="error-message">{error}</p>}
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <span className="eyebrow">Vehicle Damage Claim Portal</span>
          <h1>AI Claim Assessment</h1>
        </div>
        <div className="user-strip">
          <span>{user.full_name}</span>
          <button type="button" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <nav className="nav-tabs">
        <button className={view === "assess" ? "active" : ""} onClick={() => setView("assess")}>New Assessment</button>
        {user.role === "admin" && (
          <button className={view === "admin" ? "active" : ""} onClick={() => { setView("admin"); loadClaims(); }}>Admin Dashboard</button>
        )}
        <button className={view === "history" ? "active" : ""} onClick={() => { setView("history"); loadClaims(); }}>Claim History</button>
        <button className={view === "report" ? "active" : ""} disabled={!activeResult} onClick={() => setView("report")}>Report</button>
      </nav>

      {error && <p className="error-message floating">{error}</p>}

      {view === "assess" && (
        <>
          <section className="workspace">
            <div className="panel upload-panel">
              <div className="title-block">
                <span className="eyebrow">Upload and analyze</span>
                <h2>New vehicle claim</h2>
              </div>

              <label className={`drop-zone ${preview ? "has-preview" : ""}`}>
                <input type="file" accept="image/png,image/jpeg,image/webp" onChange={handleFileChange} />
                {preview ? (
                  <img src={preview} alt="Selected vehicle preview" />
                ) : (
                  <div>
                    <strong>Upload vehicle image</strong>
                    <span>JPG, PNG, or WEBP under 12 MB</span>
                  </div>
                )}
              </label>

              <div className="controls-grid">
                <FieldSelect label="Car model" value={carModel} onChange={setCarModel} options={carModels} />
                <FieldSelect label="Damage category" value={damageCategory} onChange={setDamageCategory} options={damageCategories} />
                <FieldSelect label="Vehicle segment" value={vehicleSegment} onChange={setVehicleSegment} options={vehicleSegments} />
                <FieldSelect label="Repair workshop" value={workshopType} onChange={setWorkshopType} options={workshopTypes} />
              </div>

              <button className="primary-action" type="button" onClick={analyzeImage} disabled={loading}>
                {loading ? "Analyzing..." : "Analyze and Save Claim"}
              </button>
            </div>

            <ResultSummary result={activeResult} severityClass={severityClass} />
          </section>

          {hasResult && <AnalysisDetails result={result} />}
        </>
      )}

      {view === "history" && (
        <section className="panel">
          <div className="section-header">
            <div>
              <span className="eyebrow">Saved claims</span>
              <h2>Claim History</h2>
            </div>
            <button type="button" className="secondary-action" onClick={() => loadClaims()}>Refresh</button>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Claim</th>
                  <th>Date</th>
                  <th>Status</th>
                  <th>Model</th>
                  <th>Part</th>
                  <th>Severity</th>
                  <th>Damages</th>
                  <th>Estimate</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {claims.map((claim) => (
                  <tr key={claim.id}>
                    <td>{claim.claim_number}</td>
                    <td>{formatDate(claim.created_at)}</td>
                    <td><span className="status-badge">{claim.status}</span></td>
                    <td>{labelFromValue(carModels, claim.car_model)}</td>
                    <td>{labelFromValue(damageCategories, claim.damage_category)}</td>
                    <td>{claim.severity}</td>
                    <td>{claim.num_damages}</td>
                    <td>{claim.estimated_cost_range}</td>
                    <td>
                      <button className="link-action" type="button" onClick={() => openClaim(claim.id)}>Open</button>
                      {user.role === "admin" && claim.status !== "Approved" && (
                        <button className="link-action" type="button" onClick={() => handleApproveClaim(claim.id)}>Approve</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {claims.length === 0 && <p className="empty-state">No claims saved yet. Run a new assessment to create the first record.</p>}
        </section>
      )}

      {view === "admin" && (
        <AdminDashboard claims={claims} openClaim={openClaim} />
      )}

      {view === "report" && activeResult && (
        <section className="report-layout">
          <div className="panel report-card">
            <div className="section-header">
              <div>
                <span className="eyebrow">AI assessment report</span>
                <h2>{activeResult.claim_number || activeResult.claim?.claim_number || "Unsaved Report"}</h2>
              </div>
              <button type="button" className="secondary-action" onClick={printReport}>Print / Save PDF</button>
            </div>
            <ResultSummary result={activeResult} severityClass={severityClass} compact />
            <AnalysisDetails result={normalizeClaimResult(activeResult)} />
          </div>
        </section>
      )}
    </main>
  );
}

function ResultSummary({ result, severityClass, compact = false }) {
  const hasResult = Boolean(result);
  const costBreakdown = result?.cost_breakdown || {};
  return (
    <div className={`panel result-panel ${compact ? "embedded" : ""}`}>
      <div className="result-header">
        <span className="eyebrow">Claim Snapshot</span>
        <div className={`severity-pill ${severityClass}`}>{hasResult ? result.severity : "Waiting"}</div>
      </div>
      <div className="metric-grid">
        <Metric label="Detected damages" value={hasResult ? result.num_damages : "--"} />
        <Metric label="Severity score" value={hasResult ? result.severity_score : "--"} />
        <Metric label="Damage area" value={hasResult ? `${(result.damage_area_ratio * 100).toFixed(2)}%` : "--"} />
        <Metric label="Review" value={costBreakdown.review_required ? "Required" : hasResult ? "Low risk" : "--"} />
      </div>
      <div className="cost-band">
        <span>Estimated repair range</span>
        <strong>{hasResult ? result.estimated_cost_range : "INR --"}</strong>
        {costBreakdown.review_reason && <small>{costBreakdown.review_reason}</small>}
      </div>
      {hasResult && result.annotated_image && (
        <div className="annotated-wrap">
          <img src={`data:image/jpeg;base64,${result.annotated_image}`} alt="Detected vehicle damage" />
        </div>
      )}
    </div>
  );
}

function AnalysisDetails({ result }) {
  return (
    <section className="analysis-grid">
      <div className="panel">
        <h2>Detections and Cost</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Damage</th>
                <th>Confidence</th>
                <th>Visible area</th>
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {(result.cost_breakdown?.line_items || []).map((item, index) => (
                <tr key={`${item.damage_type}-${index}`}>
                  <td>{index + 1}</td>
                  <td>{formatLabel(item.damage_type)}</td>
                  <td>{Math.round(item.confidence * 100)}%</td>
                  <td>{(item.area_ratio * 100).toFixed(2)}%</td>
                  <td>INR {item.estimated_min.toLocaleString()} - INR {item.estimated_max.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel">
        <h2>Preprocessing Audit</h2>
        <div className="audit-list">
          {(result.preprocessing?.steps || []).map((step) => (
            <span key={step}>{step}</span>
          ))}
        </div>
        <div className="quality-grid">
          <Metric label="Brightness" value={result.preprocessing?.brightness ?? "--"} />
          <Metric label="Contrast" value={result.preprocessing?.contrast ?? "--"} />
          <Metric label="Blur score" value={result.preprocessing?.blur_score ?? "--"} />
          <Metric label="Noise score" value={result.preprocessing?.noise_score ?? "--"} />
        </div>
      </div>
    </section>
  );
}

function AdminDashboard({ claims, openClaim }) {
  const stats = buildDashboardStats(claims);
  return (
    <section className="admin-dashboard">
      <div className="dashboard-title">
        <h2>Insurance Claims Details Dashboard</h2>
      </div>

      <div className="dashboard-grid">
        <div className="dash-card chart-card">
          <h3>Claim by Data</h3>
          <p>Data is drillable. Use the + and - icon at lower left corner.</p>
          <LineChart values={stats.trend} />
        </div>

        <div className="dash-card chart-card">
          <h3>Claim by Type Age</h3>
          <Donut percent={stats.acceptanceRate} />
          <div className="legend-row">
            <span><i className="blue-dot" /> Accepted</span>
            <span><i className="orange-dot" /> Review</span>
          </div>
        </div>

        <div className="dash-card detail-card">
          <h3>Detail Data For Each Claim</h3>
          <p>This data will automatically change when mouse over summary charts. Data sorting on column header can also be performed.</p>
          <div className="summary-strip">Claimant Information Summary</div>
          <div className="table-wrap compact-table">
            <table>
              <thead>
                <tr>
                  <th>Claim ID</th>
                  <th>Policy Holder</th>
                  <th>Vehicle</th>
                  <th>Claim Type</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {claims.slice(0, 10).map((claim) => (
                  <tr key={claim.id} onClick={() => openClaim(claim.id)}>
                    <td>{claim.claim_number}</td>
                    <td>{claim.file_name || "Customer"}</td>
                    <td>{labelFromValue(carModels, claim.car_model)}</td>
                    <td>{labelFromValue(damageCategories, claim.damage_category)}</td>
                    <td>{claim.status}</td>
                  </tr>
                ))}
                {claims.length === 0 && demoRows.map((row) => (
                  <tr key={row.id}>
                    <td>{row.id}</td>
                    <td>{row.name}</td>
                    <td>{row.vehicle}</td>
                    <td>{row.type}</td>
                    <td>{row.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="dash-card chart-card">
          <h3>Count by Claim Status</h3>
          <BarChart data={stats.statusCounts} />
        </div>

        <div className="dash-card chart-card">
          <h3>Count by Claim Type</h3>
          <BarChart data={stats.categoryCounts} horizontal />
        </div>

        <div className="dash-card filter-card">
          <h3>Global Filters</h3>
          <div className="range-filter">
            <span className="range-handle left" />
            <b>24.61</b>
            <span className="range-handle right" />
          </div>
          <div className="filter-summary">
            <Metric label="Total claims" value={claims.length} />
            <Metric label="Avg estimate" value={`INR ${stats.avgEstimate.toLocaleString()}`} />
            <Metric label="Review cases" value={stats.reviewCount} />
          </div>
          <div className="filter-table">
            <span>Claim Type</span><span>Claim Status</span><span>Vehicle Segment</span>
            <b>{Object.keys(stats.categoryCounts).join(", ") || "--"}</b>
            <b>{Object.keys(stats.statusCounts).join(", ") || "--"}</b>
            <b>{Object.keys(stats.segmentCounts).join(", ") || "--"}</b>
          </div>
        </div>
      </div>
      <p className="dashboard-footnote">This graph/chart is linked to claim data, and changes automatically based on saved assessments.</p>
    </section>
  );
}

const demoRows = [
  { id: "A10064", name: "Demo Customer", vehicle: "Maruti Swift", type: "Scratch", status: "In Progress" },
  { id: "A10066", name: "Claim Holder", vehicle: "Hyundai Creta", type: "Dent", status: "Accepted" },
  { id: "A10073", name: "Policy User", vehicle: "Honda City", type: "Paint damage", status: "Denied" },
  { id: "A10142", name: "Sample Driver", vehicle: "Tata Nexon", type: "Broken glass", status: "In Progress" },
  { id: "A10227", name: "Insurance Demo", vehicle: "Kia Seltos", type: "Deformation", status: "Accepted" },
];

function FieldSelect({ label, value, onChange, options }) {
  return (
    <label>
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
    </label>
  );
}

function buildDashboardStats(claims) {
  const statusCounts = {};
  const categoryCounts = {};
  const segmentCounts = {};
  const trendMap = {};
  let totalEstimate = 0;
  let reviewCount = 0;

  claims.forEach((claim) => {
    statusCounts[claim.status] = (statusCounts[claim.status] || 0) + 1;
    const category = labelFromValue(damageCategories, claim.damage_category || "auto");
    categoryCounts[category] = (categoryCounts[category] || 0) + 1;
    segmentCounts[claim.vehicle_segment] = (segmentCounts[claim.vehicle_segment] || 0) + 1;
    totalEstimate += claim.estimated_cost_max || claim.estimated_cost_min || 0;
    if (claim.severity === "Major" || claim.severity === "Severe" || claim.estimated_cost_max > 90000) reviewCount += 1;
    const day = (claim.created_at || "").slice(5, 10) || "Today";
    trendMap[day] = (trendMap[day] || 0) + 1;
  });

  return {
    statusCounts,
    categoryCounts,
    segmentCounts,
    reviewCount,
    avgEstimate: claims.length ? Math.round(totalEstimate / claims.length) : 0,
    acceptanceRate: claims.length ? Math.round(((statusCounts.Approved || 0) / claims.length) * 100) : 42,
    trend: Object.values(trendMap).length ? Object.values(trendMap) : [3, 5, 4, 6, 5, 7, 4, 8, 6, 9, 5, 7],
  };
}

function BarChart({ data, horizontal = false }) {
  const entries = Object.entries(data).slice(0, 6);
  const fallback = horizontal
    ? [["Scratch", 4], ["Dent", 3], ["Paint", 2], ["Glass", 2]]
    : [["Denied", 2], ["In Progress", 5], ["Accepted", 8]];
  const items = entries.length ? entries : fallback;
  const max = Math.max(...items.map(([, value]) => value), 1);
  return (
    <div className={`bar-chart ${horizontal ? "horizontal" : ""}`}>
      {items.map(([label, value]) => (
        <div className="bar-item" key={label}>
          <div className="bar-track">
            <div className="bar-fill" style={horizontal ? { width: `${(value / max) * 100}%` } : { height: `${(value / max) * 100}%` }} />
          </div>
          <span>{label}</span>
        </div>
      ))}
    </div>
  );
}

function LineChart({ values }) {
  const max = Math.max(...values, 1);
  const points = values.map((value, index) => {
    const x = 8 + (index * 84) / Math.max(values.length - 1, 1);
    const y = 88 - (value / max) * 76;
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg className="line-chart" viewBox="0 0 100 100" preserveAspectRatio="none">
      <polyline points={points} fill="none" stroke="#ef4444" strokeWidth="2.8" />
      {points.split(" ").map((point) => {
        const [cx, cy] = point.split(",");
        return <circle key={point} cx={cx} cy={cy} r="1.8" fill="#ef4444" />;
      })}
    </svg>
  );
}

function Donut({ percent }) {
  return (
    <div className="donut" style={{ "--percent": `${percent}%` }}>
      <strong>{percent}%</strong>
    </div>
  );
}

function labelFromValue(options, value) {
  return options.find((option) => option.value === value)?.label || value || "--";
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function normalizeClaimResult(result) {
  if (!result) return null;
  return {
    ...result,
    model: result.model || {},
    preprocessing: result.preprocessing || {},
    cost_breakdown: result.cost_breakdown || {},
  };
}

async function apiFetch(path, { method = "GET", body, formData, token } = {}) {
  if (!API_BASE) {
    throw new Error("Backend API URL is not configured. Set REACT_APP_API_BASE to your deployed backend URL.");
  }

  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body) headers["Content-Type"] = "application/json";

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: formData || (body ? JSON.stringify(body) : undefined),
    });
  } catch (error) {
    throw new Error(`Cannot reach backend at ${API_BASE}. Start the backend locally or set REACT_APP_API_BASE for deployment.`);
  }

  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) throw new Error(data.detail || "Request failed.");
  return data;
}

function getApiBase() {
  if (process.env.REACT_APP_API_BASE) {
    return process.env.REACT_APP_API_BASE.replace(/\/$/, "");
  }
  const host = window.location.hostname;
  if (host === "localhost" || host === "127.0.0.1") {
    return "http://127.0.0.1:8000/api";
  }
  return "";
}

function formatLabel(value) {
  return String(value || "damage").replaceAll("_", " ");
}

function formatDate(value) {
  if (!value) return "--";
  return new Date(`${value}Z`).toLocaleString();
}

export default App;

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Bar, Doughnut } from "react-chartjs-2";
import {
  getOrganiserAnalyticsSummary,
  type EventAnalytics,
  type OrganiserAnalyticsSummary,
} from "../../api/analytics";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler,
);

const COLORS = {
  accent: "#e8a54b",
  accentSoft: "rgba(232, 165, 75, 0.35)",
  ok: "#5dcea0",
  okSoft: "rgba(93, 206, 160, 0.35)",
  wait: "#9aa3b2",
  waitSoft: "rgba(154, 163, 178, 0.35)",
  ink: "#e8ecf2",
  muted: "#9aa3b2",
  grid: "rgba(232, 236, 242, 0.08)",
};

function truncate(label: string, max = 18) {
  return label.length > max ? `${label.slice(0, max - 1)}…` : label;
}

function pct(rate: number) {
  return `${(rate * 100).toFixed(1)}%`;
}

function money(value: string) {
  const n = Number(value);
  if (Number.isNaN(n)) return value;
  return n.toLocaleString(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  });
}

export default function Analytics() {
  const [data, setData] = useState<OrganiserAnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getOrganiserAnalyticsSummary()
      .then((summary) => {
        if (!cancelled) setData(summary);
      })
      .catch(() => {
        if (!cancelled) setError("Could not load analytics.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const selected: EventAnalytics | null = useMemo(() => {
    if (!data || !selectedId) return null;
    return data.events.find((e) => e.event_id === selectedId) ?? null;
  }, [data, selectedId]);

  const chartEvents = useMemo(() => {
    if (!data) return [];
    // Newest first already; show up to 12 for readability
    return data.events.slice(0, 12);
  }, [data]);

  const registrationChart = useMemo(() => {
    const labels = chartEvents.map((e) => truncate(e.title));
    return {
      labels,
      datasets: [
        {
          label: "Confirmed",
          data: chartEvents.map((e) => e.confirmed_count),
          backgroundColor: COLORS.okSoft,
          borderColor: COLORS.ok,
          borderWidth: 1.5,
          borderRadius: 3,
        },
        {
          label: "Waitlisted",
          data: chartEvents.map((e) => e.waitlisted_count),
          backgroundColor: COLORS.waitSoft,
          borderColor: COLORS.wait,
          borderWidth: 1.5,
          borderRadius: 3,
        },
      ],
    };
  }, [chartEvents]);

  const revenueChart = useMemo(() => {
    return {
      labels: chartEvents.map((e) => truncate(e.title)),
      datasets: [
        {
          label: "Revenue",
          data: chartEvents.map((e) => Number(e.revenue) || 0),
          backgroundColor: COLORS.accentSoft,
          borderColor: COLORS.accent,
          borderWidth: 1.5,
          borderRadius: 3,
        },
      ],
    };
  }, [chartEvents]);

  const checkInChart = useMemo(() => {
    if (!data) {
      return { labels: [], datasets: [] };
    }
    const checkedIn = data.total_checked_in;
    const remaining = Math.max(data.total_confirmed - checkedIn, 0);
    return {
      labels: ["Checked in", "Not checked in"],
      datasets: [
        {
          data: [checkedIn, remaining],
          backgroundColor: [COLORS.okSoft, COLORS.waitSoft],
          borderColor: [COLORS.ok, COLORS.wait],
          borderWidth: 1.5,
          hoverOffset: 8,
        },
      ],
    };
  }, [data]);

  const sharedBarOptions = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index" as const, intersect: false },
      plugins: {
        legend: {
          labels: {
            color: COLORS.muted,
            boxWidth: 12,
            font: { family: "Outfit, system-ui, sans-serif", size: 12 },
          },
        },
        tooltip: {
          backgroundColor: "#161c26",
          titleColor: COLORS.ink,
          bodyColor: COLORS.muted,
          borderColor: COLORS.grid,
          borderWidth: 1,
          padding: 10,
        },
      },
      scales: {
        x: {
          ticks: {
            color: COLORS.muted,
            maxRotation: 40,
            minRotation: 0,
            font: { size: 11 },
          },
          grid: { color: COLORS.grid },
        },
        y: {
          beginAtZero: true,
          ticks: {
            color: COLORS.muted,
            precision: 0,
          },
          grid: { color: COLORS.grid },
        },
      },
      onClick: (_: unknown, elements: { index: number }[]) => {
        if (!elements.length) {
          setSelectedId(null);
          return;
        }
        const idx = elements[0].index;
        const event = chartEvents[idx];
        if (event) {
          setSelectedId((prev) =>
            prev === event.event_id ? null : event.event_id,
          );
        }
      },
    }),
    [chartEvents],
  );

  const doughnutOptions = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      cutout: "68%",
      plugins: {
        legend: {
          position: "bottom" as const,
          labels: {
            color: COLORS.muted,
            boxWidth: 12,
            font: { family: "Outfit, system-ui, sans-serif", size: 12 },
          },
        },
        tooltip: {
          backgroundColor: "#161c26",
          titleColor: COLORS.ink,
          bodyColor: COLORS.muted,
          borderColor: COLORS.grid,
          borderWidth: 1,
          padding: 10,
        },
      },
    }),
    [],
  );

  if (loading) return <p className="state-msg">Loading analytics…</p>;
  if (error) return <p className="state-msg state-msg--error">{error}</p>;
  if (!data) return null;

  const empty = data.event_count === 0;

  return (
    <div className="analytics-page">
      <header className="analytics-hero">
        <p className="page-sub analytics-hero__back">
          <Link to="/org/events">← My events</Link>
        </p>
        <div className="analytics-hero__copy">
          <h1 className="page-title">Analytics</h1>
          <p className="page-sub">
            Registrations, check-in, and estimated revenue. Click a chart bar or
            table row to focus one event.
          </p>
        </div>
      </header>

      <div className="analytics-kpis">
        <div className="analytics-kpi">
          <span className="analytics-kpi__label">Events</span>
          <strong className="analytics-kpi__value">{data.event_count}</strong>
        </div>
        <div className="analytics-kpi">
          <span className="analytics-kpi__label">Confirmed</span>
          <strong className="analytics-kpi__value">{data.total_confirmed}</strong>
        </div>
        <div className="analytics-kpi">
          <span className="analytics-kpi__label">Waitlist</span>
          <strong className="analytics-kpi__value">{data.total_waitlisted}</strong>
        </div>
        <div className="analytics-kpi">
          <span className="analytics-kpi__label">Check-in rate</span>
          <strong className="analytics-kpi__value">
            {pct(data.overall_check_in_rate)}
          </strong>
        </div>
        <div className="analytics-kpi analytics-kpi--accent">
          <span className="analytics-kpi__label">Revenue</span>
          <strong className="analytics-kpi__value">
            {money(data.total_revenue)}
          </strong>
        </div>
      </div>

      {empty ? (
        <p className="state-msg">
          No events yet.{" "}
          <Link to="/org/events/new">Create an event</Link> to see charts.
        </p>
      ) : (
        <>
          <div className="analytics-charts">
            <section className="analytics-panel analytics-panel--main">
              <header className="analytics-panel__head">
                <h2>Registrations by event</h2>
                <p>Confirmed vs waitlisted</p>
              </header>
              <div className="analytics-chart">
                <Bar data={registrationChart} options={sharedBarOptions} />
              </div>
            </section>

            <section className="analytics-panel analytics-panel--side">
              <header className="analytics-panel__head">
                <h2>Overall check-in</h2>
                <p>
                  {data.total_checked_in} of {data.total_confirmed} confirmed
                </p>
              </header>
              <div className="analytics-chart analytics-chart--donut">
                <Doughnut data={checkInChart} options={doughnutOptions} />
                <div className="analytics-donut-center">
                  <span>{pct(data.overall_check_in_rate)}</span>
                  <small>checked in</small>
                </div>
              </div>
            </section>

            <section className="analytics-panel analytics-panel--main">
              <header className="analytics-panel__head">
                <h2>Estimated revenue</h2>
                <p>price × confirmed registrations</p>
              </header>
              <div className="analytics-chart">
                <Bar data={revenueChart} options={sharedBarOptions} />
              </div>
            </section>

            <section className="analytics-panel analytics-panel--side analytics-panel--focus">
              <header className="analytics-panel__head">
                <h2>{selected ? "Focused event" : "Snapshot"}</h2>
                <p>
                  {selected
                    ? "Selected from chart or table"
                    : "Click a bar to inspect one event"}
                </p>
              </header>

              {selected ? (
                <div className="analytics-snapshot">
                  <h3 className="analytics-snapshot__title">{selected.title}</h3>
                  <p className="analytics-snapshot__meta">
                    {selected.status} · {selected.max_capacity} capacity
                  </p>
                  <dl className="analytics-snapshot__stats">
                    <div>
                      <dt>Confirmed</dt>
                      <dd>{selected.confirmed_count}</dd>
                    </div>
                    <div>
                      <dt>Waitlist</dt>
                      <dd>{selected.waitlisted_count}</dd>
                    </div>
                    <div>
                      <dt>Check-in</dt>
                      <dd>{pct(selected.check_in_rate)}</dd>
                    </div>
                    <div>
                      <dt>Revenue</dt>
                      <dd>{money(selected.revenue)}</dd>
                    </div>
                  </dl>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() => setSelectedId(null)}
                  >
                    Clear focus
                  </button>
                </div>
              ) : (
                <div className="analytics-snapshot analytics-snapshot--idle">
                  <dl className="analytics-snapshot__stats">
                    <div>
                      <dt>Total confirmed</dt>
                      <dd>{data.total_confirmed}</dd>
                    </div>
                    <div>
                      <dt>Total waitlist</dt>
                      <dd>{data.total_waitlisted}</dd>
                    </div>
                    <div>
                      <dt>Checked in</dt>
                      <dd>{data.total_checked_in}</dd>
                    </div>
                    <div>
                      <dt>Est. revenue</dt>
                      <dd>{money(data.total_revenue)}</dd>
                    </div>
                  </dl>
                </div>
              )}
            </section>
          </div>

          <section className="analytics-table-wrap">
            <div className="analytics-table-head">
              <h2 className="analytics-section-title">All events</h2>
              <p className="page-sub">Click a row to sync the focus panel</p>
            </div>
            <table className="analytics-table">
              <thead>
                <tr>
                  <th>Event</th>
                  <th>Status</th>
                  <th>Confirmed</th>
                  <th>Waitlist</th>
                  <th>Check-in</th>
                  <th>Revenue</th>
                </tr>
              </thead>
              <tbody>
                {data.events.map((e) => (
                  <tr
                    key={e.event_id}
                    className={
                      selectedId === e.event_id
                        ? "analytics-table__row--active"
                        : undefined
                    }
                    onClick={() =>
                      setSelectedId((prev) =>
                        prev === e.event_id ? null : e.event_id,
                      )
                    }
                  >
                    <td>{e.title}</td>
                    <td>
                      <span className="status-chip status-chip--compact">
                        {e.status}
                      </span>
                    </td>
                    <td>{e.confirmed_count}</td>
                    <td>{e.waitlisted_count}</td>
                    <td>{pct(e.check_in_rate)}</td>
                    <td>{money(e.revenue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      )}
    </div>
  );
}

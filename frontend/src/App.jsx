
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Bell,
  ChartNoAxesCombined,
  CircleDollarSign,
  Clock3,
  Database,
  LayoutDashboard,
  Settings,
  ShieldAlert,
  Zap,
} from "lucide-react";

const stats = [
  {
    label: "ORDERS PROCESSED",
    value: "10,000",
    change: "+12.8%",
    icon: Activity,
  },
  {
    label: "THROUGHPUT",
    value: "1,112",
    suffix: "orders/sec",
    change: "+8.4%",
    icon: Zap,
  },
  {
    label: "NATIVE LATENCY",
    value: "400",
    suffix: "ns",
    change: "-5.2%",
    icon: Clock3,
  },
  {
    label: "EXECUTED TRADES",
    value: "8,707",
    change: "+18.2%",
    icon: CircleDollarSign,
  },
];

const orderBook = [
  { id: 9998, price: "50,098", qty: 99, side: "ASK" },
  { id: 9996, price: "50,096", qty: 97, side: "ASK" },
  { id: 9994, price: "50,094", qty: 95, side: "ASK" },
  { id: 9992, price: "50,092", qty: 93, side: "ASK" },
  { id: 9997, price: "50,097", qty: 1, side: "BID" },
  { id: 9995, price: "50,095", qty: 1, side: "BID" },
  { id: 9993, price: "50,093", qty: 1, side: "BID" },
  { id: 9991, price: "50,091", qty: 1, side: "BID" },
];

const trades = [
  [9999, 9998, "50,098", 99],
  [9997, 9996, "50,096", 97],
  [9995, 9994, "50,094", 95],
  [9993, 9992, "50,092", 93],
  [9991, 9990, "50,090", 91],
];

const whales = [
  { id: 9999, side: "BUY", price: "50,099", qty: 100 },
  { id: 9998, side: "SELL", price: "50,098", qty: 99 },
  { id: 9997, side: "BUY", price: "50,097", qty: 98 },
  { id: 9996, side: "SELL", price: "50,096", qty: 97 },
];

function StatCard({ item }) {
  const Icon = item.icon;

  return (
    <div className="rounded-xl border border-slate-800 bg-[#101827] p-5">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold tracking-wider text-slate-400">
          {item.label}
        </p>
        <Icon size={19} className="text-cyan-400" />
      </div>

      <div className="mt-4 flex items-baseline gap-2">
        <span className="text-2xl font-bold text-white">{item.value}</span>
        {item.suffix && (
          <span className="text-xs text-slate-400">{item.suffix}</span>
        )}
      </div>

      <p className="mt-3 text-xs text-emerald-400">{item.change} from baseline</p>
    </div>
  );
}

function SectionTitle({ title, subtitle }) {
  return (
    <div className="mb-4">
      <h2 className="text-sm font-bold tracking-wide text-white">{title}</h2>
      {subtitle && <p className="mt-1 text-xs text-slate-500">{subtitle}</p>}
    </div>
  );
}

function App() {
  return (
    <div className="min-h-screen bg-[#080d18] text-slate-200">
      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside className="hidden w-60 shrink-0 border-r border-slate-800 bg-[#0b1220] p-5 lg:flex lg:flex-col">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-cyan-500/15 p-2 text-cyan-400">
              <Zap size={23} />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-wide text-white">
                CHRONOS<span className="text-cyan-400">MATCH</span>
              </h1>
              <p className="text-[10px] tracking-[0.2em] text-slate-500">
                TRADING ENGINE
              </p>
            </div>
          </div>

          <p className="mb-3 mt-10 text-[10px] font-bold tracking-[0.2em] text-slate-500">
            WORKSPACE
          </p>

          <nav className="space-y-2">
            <div className="flex items-center gap-3 rounded-lg border border-cyan-400/20 bg-cyan-400/10 px-3 py-3 text-sm font-semibold text-cyan-300">
              <LayoutDashboard size={18} />
              Dashboard
            </div>
            <div className="flex items-center gap-3 rounded-lg px-3 py-3 text-sm text-slate-400">
              <ChartNoAxesCombined size={18} />
              Market Overview
            </div>
            <div className="flex items-center gap-3 rounded-lg px-3 py-3 text-sm text-slate-400">
              <Database size={18} />
              Trade Ledger
            </div>
            <div className="flex items-center gap-3 rounded-lg px-3 py-3 text-sm text-slate-400">
              <ShieldAlert size={18} />
              Whale Monitor
            </div>
          </nav>

          <div className="mt-auto rounded-xl border border-slate-800 bg-[#101827] p-4">
            <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              ENGINE READY
            </div>
            <p className="mt-2 text-xs leading-5 text-slate-500">
              ChronosMatch simulation environment
            </p>
          </div>
        </aside>

        {/* Main content */}
        <main className="min-w-0 flex-1">
          {/* Top bar */}
          <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 bg-[#0b1220] px-5 py-4 md:px-8">
            <div>
              <p className="text-xs text-slate-500">WORKSPACE / OVERVIEW</p>
              <h2 className="mt-1 text-lg font-bold text-white">
                Trading Dashboard
              </h2>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-400">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                SYSTEM ONLINE
              </div>
              <Bell size={19} className="text-slate-400" />
              <Settings size={19} className="text-slate-400" />
            </div>
          </header>

          <div className="space-y-6 p-5 md:p-8">
            {/* Heading */}
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h1 className="text-2xl font-bold text-white">
                  Market Overview
                </h1>
                <p className="mt-1 text-sm text-slate-400">
                  Real-time engine performance and market activity
                </p>
              </div>

              <div className="rounded-lg border border-slate-700 bg-[#101827] px-4 py-2 text-xs text-slate-300">
                SIMULATION MODE
              </div>
            </div>

            {/* Metrics */}
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {stats.map((item) => (
                <StatCard key={item.label} item={item} />
              ))}
            </div>

            {/* Chart and order book */}
            <div className="grid gap-5 xl:grid-cols-3">
              <section className="rounded-xl border border-slate-800 bg-[#101827] p-5 xl:col-span-2">
                <SectionTitle
                  title="ENGINE PERFORMANCE"
                  subtitle="Illustrative market activity"
                />

                <div className="flex items-center gap-5 text-xs">
                  <span className="flex items-center gap-2 text-cyan-400">
                    <span className="h-2 w-2 rounded-full bg-cyan-400" />
                    BUY VOLUME
                  </span>
                  <span className="flex items-center gap-2 text-violet-400">
                    <span className="h-2 w-2 rounded-full bg-violet-400" />
                    SELL VOLUME
                  </span>
                </div>

                <div className="mt-5 h-52 w-full">
                  <svg
                    viewBox="0 0 700 190"
                    preserveAspectRatio="none"
                    className="h-full w-full"
                  >
                    {[35, 80, 125, 170].map((y) => (
                      <line
                        key={y}
                        x1="0"
                        y1={y}
                        x2="700"
                        y2={y}
                        stroke="#263449"
                        strokeDasharray="4 6"
                      />
                    ))}

                    <path
                      d="M0 140 L65 120 L125 133 L190 80 L255 100 L320 60 L385 88 L450 48 L515 75 L580 35 L640 55 L700 20"
                      fill="none"
                      stroke="#22d3ee"
                      strokeWidth="3"
                    />
                    <path
                      d="M0 160 L65 145 L125 155 L190 125 L255 140 L320 105 L385 120 L450 95 L515 115 L580 80 L640 95 L700 70"
                      fill="none"
                      stroke="#a78bfa"
                      strokeWidth="2"
                    />
                  </svg>
                </div>

                <div className="mt-3 flex justify-between text-[10px] text-slate-500">
                  <span>09:00</span>
                  <span>10:00</span>
                  <span>11:00</span>
                  <span>12:00</span>
                  <span>13:00</span>
                  <span>14:00</span>
                </div>
              </section>

              <section className="rounded-xl border border-slate-800 bg-[#101827] p-5">
                <SectionTitle
                  title="LIVE ORDER BOOK"
                  subtitle="Top market orders"
                />

                <div className="mb-3 grid grid-cols-3 text-[10px] font-bold tracking-wider text-slate-500">
                  <span>ORDER ID</span>
                  <span className="text-right">PRICE</span>
                  <span className="text-right">QUANTITY</span>
                </div>

                <div className="space-y-2">
                  {orderBook.map((order) => (
                    <div
                      key={order.id}
                      className="relative grid grid-cols-3 items-center text-xs"
                    >
                      <span className="text-slate-400">{order.id}</span>
                      <span
                        className={`text-right font-semibold ${
                          order.side === "BID"
                            ? "text-emerald-400"
                            : "text-rose-400"
                        }`}
                      >
                        {order.price}
                      </span>
                      <span className="text-right text-slate-300">
                        {order.qty}
                      </span>
                    </div>
                  ))}
                </div>

                <div className="mt-5 rounded-lg bg-[#0b1220] p-3 text-center">
                  <p className="text-[10px] tracking-wider text-slate-500">
                    BEST BID
                  </p>
                  <p className="mt-1 font-bold text-emerald-400">50,097</p>
                </div>
              </section>
            </div>

            {/* Trades and alerts */}
            <div className="grid gap-5 xl:grid-cols-2">
              <section className="rounded-xl border border-slate-800 bg-[#101827] p-5">
                <SectionTitle
                  title="RECENT EXECUTED TRADES"
                  subtitle="Latest matching engine executions"
                />

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="text-[10px] tracking-wider text-slate-500">
                      <tr className="border-b border-slate-800">
                        <th className="pb-3">BUY ID</th>
                        <th className="pb-3">SELL ID</th>
                        <th className="pb-3 text-right">PRICE</th>
                        <th className="pb-3 text-right">QTY</th>
                      </tr>
                    </thead>
                    <tbody>
                      {trades.map((trade) => (
                        <tr
                          key={trade[0]}
                          className="border-b border-slate-800/60"
                        >
                          <td className="py-3 text-slate-300">{trade[0]}</td>
                          <td className="py-3 text-slate-300">{trade[1]}</td>
                          <td className="py-3 text-right text-cyan-400">
                            {trade[2]}
                          </td>
                          <td className="py-3 text-right">{trade[3]}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              <section className="rounded-xl border border-slate-800 bg-[#101827] p-5">
                <SectionTitle
                  title="WHALE ORDER MONITOR"
                  subtitle="Large order detection · Threshold 90"
                />

                <div className="space-y-3">
                  {whales.map((whale) => (
                    <div
                      key={whale.id}
                      className="flex items-center justify-between gap-3 rounded-lg border border-rose-500/10 bg-rose-500/[0.04] p-3"
                    >
                      <div className="flex items-center gap-3">
                        <div className="rounded-lg bg-rose-500/10 p-2 text-rose-400">
                          <ShieldAlert size={17} />
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-white">
                            Order #{whale.id}
                          </p>
                          <p className="mt-1 text-[10px] text-slate-500">
                            {whale.side} · Price {whale.price}
                          </p>
                        </div>
                      </div>

                      <div className="text-right">
                        <p className="font-bold text-rose-400">
                          {whale.qty} units
                        </p>
                        <p className="mt-1 text-[9px] tracking-wider text-rose-400">
                          WHALE DETECTED
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            </div>

            {/* Footer */}
            <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 pt-5 text-[10px] text-slate-500">
              <span>CHRONOSMATCH · ZERO-COPY TRADING ENGINE</span>
              <span className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                FRONTEND PREVIEW
              </span>
            </footer>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;

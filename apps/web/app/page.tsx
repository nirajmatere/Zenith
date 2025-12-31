export default function Home() {
  return (
    <main style={{ padding: 24, fontFamily: "ui-sans-serif, system-ui" }}>
      <h1 style={{ fontSize: 28, margin: 0 }}>Zenith</h1>
      <p style={{ marginTop: 8 }}>Bootstrap ready. Next: auth, org onboarding, NTA-style exam UI.</p>
      <ul>
        <li><a href="http://localhost:8000/health">API health</a></li>
        <li><a href="http://localhost:8000/docs">API docs</a></li>
      </ul>
    </main>
  );
}

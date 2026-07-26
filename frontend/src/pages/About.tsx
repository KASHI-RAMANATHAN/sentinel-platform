export default function About() {
  return (
    <>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-black dark:text-white">About Project</h1>
          <p className="mt-1.5 text-[10px] font-mono font-semibold uppercase tracking-wider text-black/60 dark:text-white/60">
            Sentinel Security Console Details
          </p>
        </div>
      </div>

      <div className="mt-6 flex flex-col gap-6 max-w-2xl text-black dark:text-white">
        <div className="border border-black/20 p-6 dark:border-white/20 rounded-none bg-transparent">
          <h2 className="text-lg font-bold mb-2">Problem Statement</h2>
          <p className="text-sm text-black/80 dark:text-white/80">AI-Powered Behavioral Anomaly Detection for Cybersecurity</p>
        </div>

        <div className="border border-black/20 p-6 dark:border-white/20 rounded-none bg-transparent">
          <h2 className="text-lg font-bold mb-2">Description</h2>
          <p className="text-sm text-black/80 dark:text-white/80 leading-relaxed">
            Developed an AI-powered cybersecurity platform that detects behavioral anomalies in enterprise logs using machine learning and explainable AI. The system performs anomaly detection, attack classification, and risk scoring, presenting results through a real-time SOC dashboard with alert management and investigation workflows. Built using React, FastAPI, Firebase, and Python.
          </p>
        </div>

        <div className="border border-black/20 p-6 dark:border-white/20 rounded-none bg-transparent">
          <h2 className="text-lg font-bold mb-4">Developer Contact</h2>
          <ul className="space-y-2 text-sm text-black/80 dark:text-white/80">
            <li><strong>Name:</strong> Kashi Ramanathan Valliappa</li>
            <li><strong>Contact:</strong> kashiramanathan2@gmail.com</li>
            <li>
              <strong>LinkedIn:</strong>{' '}
              <a href="https://www.linkedin.com/in/kashi-ramanathan-v-932016225/" target="_blank" rel="noreferrer" className="underline hover:text-black dark:hover:text-white">
                https://www.linkedin.com/in/kashi-ramanathan-v-932016225/
              </a>
            </li>
            <li>
              <strong>GitHub:</strong>{' '}
              <a href="https://github.com/KASHI-RAMANATHAN" target="_blank" rel="noreferrer" className="underline hover:text-black dark:hover:text-white">
                https://github.com/KASHI-RAMANATHAN
              </a>
            </li>
          </ul>
        </div>
      </div>
    </>
  );
}

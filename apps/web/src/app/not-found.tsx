import Link from "next/link";

export default function NotFound() {
  return <main className="centered-state"><span>404</span><h1>This operational surface does not exist.</h1><p>Return to the command center to continue the demo.</p><Link className="button button-primary" href="/dashboard">Open command center</Link></main>;
}

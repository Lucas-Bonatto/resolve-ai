"use client";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <main className="centered-state"><span>RECOVERABLE ERROR</span><h1>The interface could not load this view.</h1><p>No action was executed. Retry, or verify that the local API is running on port 8000.</p><button className="button button-primary" onClick={reset}>Try again</button></main>;
}

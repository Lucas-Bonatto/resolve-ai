"use client";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <main className="centered-state"><span>ERRO RECUPERÁVEL</span><h1>A interface não conseguiu carregar esta visualização.</h1><p>Nenhuma ação foi executada. Tente novamente ou verifique se a API local está ativa na porta 8000.</p><button className="button button-primary" onClick={reset}>Tentar novamente</button></main>;
}

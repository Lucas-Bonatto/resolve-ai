import Link from "next/link";

export default function NotFound() {
  return <main className="centered-state"><span>404</span><h1>Esta área operacional não existe.</h1><p>Volte à Central de operações para continuar a demonstração.</p><Link className="button button-primary" href="/dashboard">Abrir Central de operações</Link></main>;
}

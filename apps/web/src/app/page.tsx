import Link from "next/link";
import { ArrowIcon, CheckIcon, MarkIcon } from "@/components/icons";
import { SectionTitle, StatusBadge } from "@/components/ui";

const workflow = [
  { number: "01", title: "Coletar evidências", body: "Consultar ferramentas empresariais limitadas e transformar logs, transações, implantações e testes em evidências inspecionáveis.", tag: "LEITURA · AUTOMÁTICO" },
  { number: "02", title: "Testar hipóteses", body: "Manter explicações concorrentes visíveis, atualizar a confiança e rejeitar conclusões sem suporte das evidências.", tag: "TIPADO · RASTREÁVEL" },
  { number: "03", title: "Solicitar aprovação", body: "Vincular a aprovação da ação crítica ao incidente, à chamada da ferramenta, aos argumentos exatos, ao revisor e à expiração.", tag: "CRÍTICO · PAUSADO" },
  { number: "04", title: "Comprovar o resultado", body: "Validar a remediação e resolver somente quando verificações controladas confirmarem a recuperação.", tag: "VALIDADO · AUDITADO" },
];

export default function LandingPage() {
  return <>
    <a className="skip-link" href="#public-content">Pular para o conteúdo principal</a>
    <main className="public-page" id="public-content" tabIndex={-1}>
    <header className="public-nav">
      <Link href="/" className="brand"><span className="brand-mark"><MarkIcon /></span><span>Resolve<span>AI</span></span></Link>
      <nav aria-label="Navegação pública"><a href="#workflow">Como funciona</a><a href="#security">Segurança</a><Link href="/evals">Avaliações</Link><Link href="/audit">Auditoria</Link></nav>
      <Link href="/dashboard" className="button button-secondary">Explorar demonstração <ArrowIcon /></Link>
    </header>

    <section className="hero">
      <div className="hero-copy">
        <div className="hero-kicker"><span /> Inteligência agentiva limitada para incidentes e operações</div>
        <h1>Incidentes resolvidos com <em>evidências.</em></h1>
        <p>Um fluxo de IA limitado e auditável que investiga problemas operacionais, usa ferramentas empresariais, propõe ações, valida soluções e mantém pessoas no controle.</p>
        <div className="hero-actions"><Link href="/incidents/INC-2026-0042" className="button button-primary">Iniciar demonstração interativa <ArrowIcon /></Link><a href="#architecture" className="button button-secondary">Ver arquitetura</a></div>
        <div className="trust-row"><span><CheckIcon /> Funciona sem chave de API</span><span><CheckIcon /> Sem dados reais de clientes</span><span><CheckIcon /> Ações críticas exigem aprovação</span></div>
      </div>

      <div className="hero-console" aria-label="Prévia do cenário principal de incidente">
        <div className="console-bar"><div><i /><i /><i /></div><span>Prévia do cenário · Simulado · SIMULATED</span></div>
        <div className="console-body">
          <aside className="console-summary"><small>Incidente ativo</small><h3>Pagamentos aprovados continuam pendentes</h3><StatusBadge tone="critical">SEV-1</StatusBadge><div className="console-stat"><small>Afetadas</small><b>37 transações</b></div><div className="console-stat"><small>Serviço</small><b>webhook-worker</b></div><div className="console-stat"><small>Estado do agente</small><b>Aguardando aprovação</b></div></aside>
          <section className="console-timeline"><h4>Linha do tempo da investigação</h4>
            <div className="preview-event"><b>Busca de transações concluída</b><p>37 pagamentos aprovados continuam pendentes.</p></div>
            <div className="preview-event"><b>Evidências correlacionadas</b><p>Erros de esquema começaram quatro minutos após a dep_184.</p></div>
            <div className="preview-event"><b>Regressão reproduzida</b><p>O payload legado paymentStatus falha na versão ativa.</p></div>
            <div className="preview-event active"><b>Decisão humana necessária</b><p>A reversão da dep_184 é crítica e está pausada para revisão.</p></div>
          </section>
        </div>
      </div>
    </section>

    <section className="proof-strip" aria-label="Comprovações de engenharia"><div className="proof-inner">
      <div className="proof-item"><strong>Evidências primeiro</strong><span>Todo diagnóstico cita IDs inspecionáveis</span></div>
      <div className="proof-item"><strong>Política de falha segura</strong><span>A autorização permanece fora do modelo</span></div>
      <div className="proof-item"><strong>40 cenários de avaliação</strong><span>Incluindo cinco defesas contra injeção</span></div>
      <div className="proof-item"><strong>Ferramentas MCP abertas</strong><span>Servidor tipado de operações da NovaPay</span></div>
    </div></section>

    <section className="landing-section" id="workflow"><SectionTitle eyebrow="Um fluxo verificável" title="Do sinal à resolução, cada etapa deixa evidências." description="ResolveAI usa um fluxo agentivo limitado, coordenado pela aplicação — não uma interface de chat. Estado do fluxo, chamadas de ferramentas, decisões de política e aprovações humanas são objetos explícitos do produto." />
      <div className="workflow-grid">{workflow.map(item => <article className="workflow-card" key={item.number}><span>{item.number}</span><h3>{item.title}</h3><p>{item.body}</p><b>{item.tag}</b></article>)}</div>
    </section>

    <section className="approval-section" id="security"><div className="approval-inner">
      <SectionTitle eyebrow="Pessoas permanecem no controle" title="O raciocínio pode sugerir. Somente a política pode autorizar." description="O gateway de aprovação revalida risco, escopo, expiração, incidente, chamada da ferramenta e o hash dos argumentos exatos antes de permitir um efeito crítico." />
      <article className="approval-card-demo"><header><StatusBadge tone="warning">Aprovação necessária</StatusBadge><StatusBadge tone="critical">Escrita crítica</StatusBadge></header><h3>Reverter webhook-worker para dep_183</h3><p>As falhas começaram após a dep_184 e um teste controlado reproduziu o defeito do parser.</p><div className="approval-evidence"><span>DEPLOY-184</span><span>LOG-291</span><span>TEST-012</span></div><div className="approval-actions-demo" aria-label="Prévia da decisão"><span className="button button-secondary">Rejeitar</span><span className="button button-success">Aprovar ação exata</span></div></article>
    </div></section>

    <section className="landing-section" id="architecture"><SectionTitle eyebrow="Arquitetura" title="Agentivo onde é útil. Determinístico onde é necessário." description="O FastAPI controla fluxo, permissões, evidências e auditoria. O OpenAI Agents SDK produz análises tipadas. Um provedor determinístico usa os mesmos contratos em demonstrações locais sem custo." />
      <div className="workflow-grid">
        <article className="workflow-card"><span>APP</span><h3>Central em Next.js</h3><p>Superfícies priorizando o servidor, com interações focadas para eventos e decisões ao vivo.</p><b>APP ROUTER · TYPESCRIPT</b></article>
        <article className="workflow-card"><span>NÚCLEO</span><h3>Coordenador FastAPI</h3><p>Transições de estado explícitas, evidências validadas, ferramentas limitadas e eventos por SSE.</p><b>PYDANTIC · CAMADA DE DOMÍNIO</b></article>
        <article className="workflow-card"><span>IA</span><h3>Limite do provedor</h3><p>Os provedores determinístico e OpenAI retornam o mesmo contrato estruturado de diagnóstico.</p><b>AGENTS SDK · AVALIAÇÕES</b></article>
        <article className="workflow-card"><span>FERR.</span><h3>NovaPay MCP</h3><p>Um servidor MCP v2 independente expõe dados operacionais fictícios com esquemas tipados e auditoria.</p><b>MCP · GATEWAY DE POLÍTICA</b></article>
      </div>
    </section>

    <section className="landing-section open-source"><SectionTitle eyebrow="Estudo de caso de engenharia open source" title="Inspecione as afirmações. Reproduza os resultados." description="A demonstração é fictícia. A arquitetura, os invariantes de segurança, o executor de avaliações e os testes são reais e inspecionáveis." /><div className="hero-actions"><Link href="/dashboard" className="button button-primary">Abrir Central de operações <ArrowIcon /></Link><Link href="/evals" className="button button-secondary">Ver Central de avaliações</Link></div></section>
    <footer className="public-footer"><Link href="/" className="brand"><span className="brand-mark"><MarkIcon /></span><span>Resolve<span>AI</span></span></Link><span>Simulação fictícia da NovaPay · Agentes podem raciocinar. Sistemas devem verificar.</span></footer>
    </main>
  </>;
}

import { AppShell } from "@/components/app-shell";
import { LockIcon } from "@/components/icons";
import { StatusBadge } from "@/components/ui";

export const metadata = { title: "Central de segurança" };

export default function SecurityPage() {
  return <AppShell title="Central de segurança" description="Limites determinísticos de permissão, defesas contra injeção e ações bloqueadas.">
    <section style={{ marginTop: 24 }}><div className="permission-grid">
      <article className="permission-card"><StatusBadge tone="success">Verde · Leitura</StatusBadge><h3>Acesso automático e limitado</h3><p>Consultas validadas podem inspecionar dados operacionais fictícios sem interrupção humana.</p><ul><li>Pesquisar transações</li><li>Inspecionar logs da aplicação</li><li>Ler implantações</li><li>Pesquisar a base de conhecimento</li></ul></article>
      <article className="permission-card yellow"><StatusBadge tone="warning">Amarelo · Escrita segura</StatusBadge><h3>Automático e auditado</h3><p>Artefatos internos não críticos podem ser preparados, mas toda escrita deixa um registro de auditoria.</p><ul><li>Adicionar nota ao incidente</li><li>Preparar atualização ao cliente</li><li>Preparar tarefa de engenharia</li><li>Gerar plano de remediação</li></ul></article>
      <article className="permission-card red"><StatusBadge tone="critical">Vermelho · Escrita crítica</StatusBadge><h3>Aprovação explícita necessária</h3><p>O fluxo é pausado. A aprovação é vinculada aos argumentos exatos, ao ator, ao incidente e à expiração.</p><ul><li>Reverter serviço</li><li>Alterar estado da transação</li><li>Enviar comunicação</li><li>Criar ou mesclar código</li></ul></article>
    </div></section>
    <section className="content-grid dashboard-main">
      <article className="panel"><header className="panel-header"><h2>Decisão recente de política</h2><StatusBadge tone="neutral">Simulado · SIMULATED</StatusBadge></header><div className="panel-body"><div className="blocked-card"><div className="blocked-icon"><LockIcon /></div><div><h3>Reversão crítica bloqueada</h3><p><code>request_service_rollback</code> · aprovação ausente · INC-2026-0042</p></div><StatusBadge tone="critical">Bloqueado</StatusBadge></div></div></article>
      <article className="panel"><header className="panel-header"><h2>Avaliação de segurança</h2><StatusBadge tone="success">5 casos</StatusBadge></header><div className="panel-body summary-list"><div><span>Injeção de prompt em conhecimento</span><b>Coberto</b></div><div><span>Texto malicioso de cliente</span><b>Coberto</b></div><div><span>Entrada de incidente contaminada</span><b>Coberto</b></div><div><span>Injeção em saída de ferramenta</span><b>Coberto</b></div><div><span>Texto falso de administrador</span><b>Coberto</b></div></div></article>
    </section>
    <article className="panel" style={{ marginTop: 16 }}><header className="panel-header"><h2 id="approval-invariants-title">Invariantes de aprovação</h2><StatusBadge tone="success">Testados</StatusBadge></header><div className="table-scroll" role="region" aria-labelledby="approval-invariants-title" tabIndex={0}><table className="data-table"><caption className="sr-only">Invariantes de aprovação</caption><thead><tr><th>Invariante</th><th>Aplicação</th><th>Comportamento em falha</th></tr></thead><tbody><tr><td><strong>Argumentos exatos</strong><small>Vínculo SHA-256 canônico</small></td><td>Motor de permissões no servidor</td><td>Falha segura</td></tr><tr><td><strong>Incidente proprietário</strong><small>Sem reutilização entre incidentes</small></td><td>Gateway de aprovação</td><td>Rejeitar e auditar</td></tr><tr><td><strong>Expiração</strong><small>Padrão de 15 minutos</small></td><td>Comparação em UTC</td><td>Marcar como expirada</td></tr><tr><td><strong>Decisão única</strong><small>Sem repetição</small></td><td>Estado consumido</td><td>Resposta de conflito</td></tr></tbody></table></div></article>
  </AppShell>;
}

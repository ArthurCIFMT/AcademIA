import { StatusMessage } from "../../ui/primitives";

export type Decision = {
  resultado: "ALLOW" | "DENY";
  motivo: string;
  comando: { estado: "CRIADO" | "ACEITO" | "FALHOU" | "CONFIRMADO" | "EXPIRADO" };
};

const denial: Record<string, string> = {
  IDENTIFICACAO_FORA_DA_JANELA: "A identificação expirou. Faça uma nova tentativa.",
  CLIENTE_INABILITADO: "A conta ou o perfil do cliente está inativo.",
  SEM_MATRICULA_VIGENTE: "O cliente precisa de uma matrícula vigente.",
  MODALIDADE_INCOMPATIVEL: "A modalidade da matrícula é incompatível com este ponto de acesso.",
  LIMITE_DIARIO: "O limite diário de entradas foi atingido.",
};

export function AccessDecisionStatus({ decision }: { decision: Decision }) {
  return <StatusMessage state={decision.resultado === "ALLOW" && decision.comando.estado !== "FALHOU" ? "success" : "conflict"}
      title={decision.resultado === "DENY" ? "Acesso negado." : "Autorização registrada."}>
      {decision.resultado === "DENY"
        ? denial[decision.motivo] ?? "A solicitação não atendeu às regras de acesso."
        : {
          ACEITO: "Comando aceito. Aguardando a passagem simulada.",
          CONFIRMADO: "Passagem simulada confirmada.",
          FALHOU: "A catraca não confirmou o comando. Tente reenviar.",
          EXPIRADO: "O comando expirou. Faça uma nova captura.",
          CRIADO: "Comando aguardando envio.",
        }[decision.comando.estado]}
  </StatusMessage>;
}

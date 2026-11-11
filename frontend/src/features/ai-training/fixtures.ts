import type { Context } from "./api";
export const sampleContext: Context = {
  execucao_id: "execution", iniciada_em: "2026-11-11T12:00:00Z", modelo: "modelo-teste", versao_prompts: "v1", regra_versao: 1, politica_alterada: false, fontes_alteradas: false,
  fontes: [{ fragmento_id: "fragment", documento_versao_id: "source-version", titulo: "Literatura de teste", origem_url: "https://example.test/livro", idioma: "pt-BR", pagina: 10, linha_inicio: null, linha_fim: null, secao: "Exercícios" }],
  contexto: { onboarding_usado_id: "onboarding", onboarding_atual_id: "onboarding", pendencias: [],
    aviso: { instrutor_designado_id: null, interno_registrado: false, email_estado: null, email_tentativas: 0 },
    treino: { ficha: { id: "version", numero: 1, origem: "IA", autor_id: null, onboarding_id: "onboarding", avaliacao_id: null, versao_base_id: null, estado_publicacao: "PUBLICADO", vigente: true, revisao: 1, publicada_em: "2026-11-11T12:00:00Z", motivo_exclusao: null, explicacao: "Orientação em português.",
      dias: [{ titulo: "Dia A", itens: [{ exercicio_id: "exercise", equipamento_ids: [], series: 3, repeticoes: "8-12", carga_kg: null, cadencia: null, intervalo_segundos: 60, observacoes: "", exercicio_snapshot: { nome: "Movimento sintético" } }] }] },
      parecer: { id: null, estado: "PENDENTE", instrutor_id: null, motivo: null, criado_em: null }, validacao: null } },
};

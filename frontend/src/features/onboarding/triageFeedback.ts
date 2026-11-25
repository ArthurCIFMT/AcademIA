const pendingHealth: Record<string, string> = {
  PENDENCIA_CONDICOES: "Confira as condições de saúde informadas e a gravidade dos relatos.",
  PENDENCIA_LIMITACOES: "Confira as informações sobre dor, lesão ou limitação e sua gravidade.",
  PENDENCIA_RESTRICAO: "Informe se recebeu orientação para restringir exercícios.",
  PENDENCIA_EVENTO: "Informe se houve um evento de saúde importante recentemente.",
  PENDENCIA_MEDICACAO: "Complete a resposta sobre uso de medicamentos junto com os demais dados de saúde.",
};

export function healthFeedback(reason: string) {
  return pendingHealth[reason];
}

export function onboardingForReason(reason?: string) {
  return "/area/cliente/onboarding" + (reason && healthFeedback(reason) ? "?etapa=saude" : "");
}

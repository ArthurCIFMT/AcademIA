import type { Role } from "../lib/api/auth";

export const areas = {
  ADMINISTRADOR: { path: "/area/administracao", label: "Administração", title: "Área administrativa" },
  ATENDENTE: { path: "/area/atendimento", label: "Atendimento", title: "Área de atendimento" },
  INSTRUTOR: { path: "/area/instrutor", label: "Instrutor", title: "Área do instrutor" },
  CLIENTE: { path: "/area/cliente", label: "Cliente", title: "Área do cliente" },
} satisfies Record<Role, { path: string; label: string; title: string }>;

export const paths = {
  clientTraining: "/area/cliente/treinos",
  clientAssistant: "/area/cliente/assistente",
  clientGeneration: "/area/cliente/treino-ia",
  clientOnboarding: "/area/cliente/onboarding",
  equipmentCatalog: "/equipamentos",
  clientEquipment: "/area/cliente/equipamentos",
  publicClasses: "/aulas",
  clientClasses: "/area/cliente/aulas",
  clientAttendance: "/area/cliente/frequencia",
  clientBilling: "/area/cliente/cobrancas",
  clientCheckout: "/area/cliente/compra-simulada",
  assignedClients: "/area/instrutor/clientes",
  reviews: "/area/instrutor/revisoes",
  instructorExercises: "/area/instrutor/exercicios",
  attendantClients: "/area/atendimento/clientes",
  attendantRecognition: "/area/atendimento/reconhecimento",
  attendantMemberships: "/area/atendimento/matriculas",
  adminClients: "/area/administracao/clientes",
  staff: "/area/administracao/funcionarios",
  assignments: "/area/administracao/designacoes",
  equipment: "/area/administracao/equipamentos",
  adminClasses: "/area/administracao/aulas",
  adminPlans: "/area/administracao/planos",
  adminExercises: "/area/administracao/exercicios",
  corpus: "/tecnico/corpus",
};

export const areaHome: Record<Role, string> = {
  ADMINISTRADOR: areas.ADMINISTRADOR.path,
  ATENDENTE: paths.attendantClients,
  INSTRUTOR: paths.assignedClients,
  CLIENTE: paths.clientTraining,
};

export const areaShortcuts: Record<Role, string[]> = {
  ADMINISTRADOR: [areaHome.ADMINISTRADOR, paths.adminClients],
  ATENDENTE: [paths.attendantClients, paths.attendantRecognition],
  INSTRUTOR: [paths.assignedClients, paths.reviews],
  CLIENTE: [paths.clientTraining, paths.clientAssistant],
};

export const occupancyPath = (role: Role) => areas[role].path + "/lotacao";
export const ownProfilePath = (role: Role) => areas[role].path + "/perfil";
export const clientAttendanceBase = (role: "ATENDENTE" | "ADMINISTRADOR") =>
  areas[role].path + "/clientes/frequencia";

type MenuItem = { path: string; label: string };

const tasks: Record<Role, MenuItem[]> = {
  CLIENTE: [
    { path: paths.clientTraining, label: "Meus treinos" },
    { path: paths.clientAttendance, label: "Minha frequência" },
    { path: paths.clientBilling, label: "Minhas cobranças" },
    { path: paths.clientCheckout, label: "Simular compra de plano" },
    { path: paths.clientAssistant, label: "Assistente" },
    { path: paths.clientOnboarding, label: "Meus dados de treino" },
    { path: paths.clientEquipment, label: "Equipamentos disponíveis" },
    { path: paths.clientClasses, label: "Agenda de aulas" },
  ],
  INSTRUTOR: [
    { path: paths.assignedClients, label: "Meus clientes" },
    { path: paths.reviews, label: "Revisões pendentes" },
    { path: paths.instructorExercises, label: "Catálogo de exercícios" },
  ],
  ATENDENTE: [
    { path: paths.attendantClients, label: "Clientes e convites" },
    { path: paths.attendantRecognition, label: "Reconhecimento facial" },
  ],
  ADMINISTRADOR: [
    { path: paths.adminClients, label: "Gerenciar clientes" },
    { path: paths.staff, label: "Gerenciar funcionários" },
    { path: paths.assignments, label: "Designações" },
    { path: paths.equipment, label: "Gerenciar equipamentos" },
    { path: paths.adminExercises, label: "Catálogo de exercícios" },
    { path: paths.adminClasses, label: "Gerenciar aulas" },
    { path: paths.adminPlans, label: "Gerenciar planos" },
  ],
};

export function areaMenu(role: Role, maintenance: boolean) {
  const items = [...tasks[role],
    { path: occupancyPath(role), label: "Lotação atual" }];
  if (role === "ADMINISTRADOR") items.unshift({ path: areaHome.ADMINISTRADOR, label: "Painel" });
  if (role === "ADMINISTRADOR" && maintenance) {
    items.push({ path: paths.corpus, label: "Curadoria técnica do RAG" });
  }
  return items;
}

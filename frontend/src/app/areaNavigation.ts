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
  assignedClients: "/area/instrutor/clientes",
  reviews: "/area/instrutor/revisoes",
  instructorExercises: "/area/instrutor/exercicios",
  attendantClients: "/area/atendimento/clientes",
  adminClients: "/area/administracao/clientes",
  staff: "/area/administracao/funcionarios",
  assignments: "/area/administracao/designacoes",
  equipment: "/area/administracao/equipamentos",
  adminExercises: "/area/administracao/exercicios",
  corpus: "/tecnico/corpus",
};

type MenuItem = { path: string; label: string };

const tasks: Record<Role, MenuItem[]> = {
  CLIENTE: [
    { path: paths.clientTraining, label: "Meus treinos" },
    { path: paths.clientAssistant, label: "Assistente" },
    { path: paths.clientOnboarding, label: "Meus dados de treino" },
    { path: paths.equipmentCatalog, label: "Equipamentos disponíveis" },
  ],
  INSTRUTOR: [
    { path: paths.assignedClients, label: "Meus clientes" },
    { path: paths.reviews, label: "Revisões pendentes" },
    { path: paths.instructorExercises, label: "Catálogo de exercícios" },
  ],
  ATENDENTE: [{ path: paths.attendantClients, label: "Clientes e convites" }],
  ADMINISTRADOR: [
    { path: paths.adminClients, label: "Gerenciar clientes" },
    { path: paths.staff, label: "Gerenciar funcionários" },
    { path: paths.assignments, label: "Designações" },
    { path: paths.equipment, label: "Gerenciar equipamentos" },
    { path: paths.adminExercises, label: "Catálogo de exercícios" },
  ],
};

export function areaMenu(role: Role, maintenance: boolean) {
  const items = [{ path: areas[role].path, label: "Início da área" }, ...tasks[role]];
  if (role === "ADMINISTRADOR" && maintenance) {
    items.push({ path: paths.corpus, label: "Curadoria técnica do RAG" });
  }
  return items;
}

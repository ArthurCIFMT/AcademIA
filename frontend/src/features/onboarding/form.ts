type Scalar = string | number | null;

type Choice = readonly [string, string];
export type Field = {
  name: string;
  label: string;
} & (
  | { kind: "number"; min: number; max: number; step: number }
  | { kind: "choice"; options: readonly Choice[] }
  | { kind: "text" | "notes"; maxLength: number; optional?: boolean }
);

const answers = [["SIM", "Sim"], ["NAO", "Não"], ["NAO_SEI", "Não sei"]] as const;
const severity = {
  name: "gravidade_declarada", label: "Gravidade declarada", kind: "choice",
  options: [["NAO_GRAVE", "Não grave"], ["GRAVE", "Grave"], ["NAO_SEI", "Não sei"]],
} as const satisfies Field;
const description = { name: "descricao", label: "Descrição", kind: "notes", maxLength: 300 } as const;

export const profileFields = [
  { name: "altura_cm", label: "Altura (cm)", kind: "number", min: 50, max: 250, step: 0.1 },
  { name: "peso_kg", label: "Peso (kg)", kind: "number", min: 20, max: 350, step: 0.1 },
  { name: "objetivo_principal", label: "Objetivo principal", kind: "choice", options: [
    ["CONDICIONAMENTO", "Condicionamento"], ["FORCA", "Força"],
    ["HIPERTROFIA", "Hipertrofia"], ["ATIVIDADE_GERAL", "Atividade geral"],
  ] },
  { name: "experiencia", label: "Experiência com exercícios", kind: "choice", options: [
    ["INICIANTE", "Iniciante"], ["INTERMEDIARIO", "Intermediário"], ["AVANCADO", "Avançado"],
  ] },
  { name: "nivel_atividade", label: "Nível de atividade atual", kind: "choice", options: [
    ["SEDENTARIO", "Sedentário"], ["LEVE", "Leve"], ["MODERADO", "Moderado"], ["ELEVADO", "Elevado"],
  ] },
  { name: "dias_semana", label: "Dias disponíveis por semana", kind: "number", min: 1, max: 6, step: 1 },
  { name: "duracao_sessao_min", label: "Tempo por sessão (minutos)", kind: "number", min: 20, max: 120, step: 1 },
] as const satisfies readonly Field[];

export const healthGroups = [
  {
    answer: { name: "possui_condicoes_saude", label: "Possui alguma condição de saúde?", kind: "choice", options: answers },
    list: "condicoes_saude", label: "Condições de saúde", item: "condição", max: 10,
    fields: [
      { name: "categoria", label: "Categoria", kind: "choice", options: [
        ["CARDIACA", "Cardíaca"], ["RESPIRATORIA", "Respiratória"], ["METABOLICA", "Metabólica"],
        ["MUSCULOESQUELETICA", "Musculoesquelética"], ["OUTRA", "Outra"],
      ] },
      description, severity,
    ],
  },
  {
    answer: { name: "usa_medicamentos", label: "Usa medicamentos?", kind: "choice", options: answers },
    list: "medicamentos", label: "Medicamentos", item: "medicamento", max: 10,
    fields: [
      { name: "nome", label: "Nome do medicamento", kind: "text", maxLength: 100 },
      { name: "observacao", label: "Observação do medicamento", kind: "notes", maxLength: 300, optional: true },
    ],
  },
  {
    answer: { name: "possui_dor_lesao_limitacao", label: "Possui dor, lesão ou limitação?", kind: "choice", options: answers },
    list: "limitacoes", label: "Dores, lesões e limitações", item: "limitação", max: 8,
    fields: [
      { name: "regiao", label: "Região do corpo", kind: "text", maxLength: 80 },
      description, severity,
    ],
  },
] as const satisfies readonly {
  answer: Field; list: string; label: string; item: string; max: number; fields: readonly Field[];
}[];

export const otherHealthFields = [
  { name: "restricao_exercicio_declarada", label: "Já recebeu alguma orientação para restringir exercícios?", kind: "choice", options: answers },
  { name: "evento_saude_importante_recente", label: "Teve algum evento de saúde importante recentemente?", kind: "choice", options: answers },
  { name: "observacoes", label: "Outras observações", kind: "notes", maxLength: 1000, optional: true },
] as const satisfies readonly Field[];

type ScalarKey = (typeof profileFields | typeof otherHealthFields)[number]["name"]
  | (typeof healthGroups)[number]["answer"]["name"];
type ListKey = (typeof healthGroups)[number]["list"];
type Row = Record<string, Scalar>;
export type FormData = Partial<Record<ScalarKey, Scalar> & Record<ListKey, Row[] | null>>;

function normalizeField(field: Field, value: Scalar | undefined, complete: boolean): Scalar | undefined {
  if (value === null || value === undefined || value === "") {
    if (field.kind !== "notes" || !field.optional) return value === "" ? null : value;
    return complete ? "" : value;
  }
  if (field.kind === "number") {
    const number = Number(value);
    const units = number / field.step;
    if (Number.isFinite(number) && number >= field.min && number <= field.max &&
        Math.abs(units - Math.round(units)) < 1e-9) return number;
    throw new Error(field.label + " deve ficar entre " + field.min + " e " + field.max +
      (field.step === 1 ? " e ser um número inteiro." : " e ter até uma casa decimal."));
  }
  if (field.kind === "choice") {
    if (field.options.some(([option]) => option === value)) return value;
    throw new Error("Selecione uma opção válida em " + field.label + ".");
  }
  const text = String(value).trim();
  if (Array.from(text).length > field.maxLength) {
    throw new Error(field.label + " excede " + field.maxLength + " caracteres.");
  }
  return text || (field.optional ? "" : null);
}

function checked(field: Field, value: Scalar | undefined, complete: boolean): Scalar | undefined {
  const normalized = normalizeField(field, value, complete);
  if (complete && normalized == null) throw new Error("Preencha " + field.label + ".");
  return normalized;
}

export function prepareForm(form: FormData, complete: boolean): FormData {
  const result: FormData = {};
  for (const field of [...profileFields, ...healthGroups.map(({ answer }) => answer), ...otherHealthFields]) {
    const value = checked(field, form[field.name], complete);
    if (value !== undefined) result[field.name] = value;
  }
  for (const group of healthGroups) {
    const rows = form[group.list];
    if (form[group.answer.name] !== "SIM") {
      if (complete || rows != null) result[group.list] = [];
      else if (rows === null) result[group.list] = null;
      continue;
    }
    if (complete && !rows?.length) throw new Error("Adicione pelo menos um registro em " + group.label + ".");
    if (rows === null) result[group.list] = null;
    if (!rows) continue;
    if (rows.length > group.max) throw new Error(group.label + " excede o limite de registros.");
    result[group.list] = rows.map((row) => {
      const item: Row = {};
      for (const field of group.fields) {
        const value = checked(field, row[field.name], complete);
        if (value !== undefined) item[field.name] = value;
      }
      return item;
    });
  }
  return result;
}

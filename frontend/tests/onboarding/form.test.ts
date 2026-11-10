// @vitest-environment node
import { readFileSync } from "node:fs";
import { URL } from "node:url";
import { expect, test } from "vitest";

import { healthGroups, otherHealthFields, prepareForm, profileFields } from "../../src/features/onboarding/form";

const schema = JSON.parse(readFileSync(new URL("../../../docs/requisitos/schemas/onboarding-v1.schema.json", import.meta.url), "utf-8"));
const cases = JSON.parse(readFileSync(new URL("../../../docs/testes/contratos-onboarding-v1.json", import.meta.url), "utf-8"));

test("campos, opções, limites e grupos correspondem ao schema aprovado", () => {
  const fields = [...profileFields, ...healthGroups.map((group) => group.answer), ...otherHealthFields];
  expect(new Set([...fields.map((field) => field.name), ...healthGroups.map((group) => group.list)]))
    .toEqual(new Set(schema.required));
  const inspect = (field: (typeof fields)[number] | (typeof healthGroups)[number]["fields"][number], definition: Record<string, unknown>) => {
    if (field.kind === "choice") expect(field.options.map(([key]) => key)).toEqual(definition.enum);
    if (field.kind === "number") {
      expect([field.min, field.max, field.step]).toEqual([definition.minimum, definition.maximum, definition.multipleOf ?? 1]);
    }
    if (field.kind === "text" || field.kind === "notes") expect(field.maxLength).toBe(definition.maxLength);
  };
  for (const field of fields) inspect(field, schema.properties[field.name]);
  for (const group of healthGroups) {
    const list = schema.properties[group.list];
    expect(group.max).toBe(list.maxItems);
    expect(new Set(group.fields.map((field) => field.name))).toEqual(new Set(list.items.required));
    for (const field of group.fields) inspect(field, list.items.properties[field.name]);
  }
});

test("rascunho distingue campo ausente, valor nulo e desconhecido", () => {
  expect(prepareForm({}, false)).toEqual({});
  expect(prepareForm({ peso_kg: null, usa_medicamentos: "NAO_SEI" }, false))
    .toEqual({ peso_kg: null, usa_medicamentos: "NAO_SEI" });
  expect(prepareForm({ altura_cm: "172.4" }, false)).toEqual({ altura_cm: 172.4 });
  expect(() => prepareForm({ altura_cm: "172.42" }, false)).toThrow(/até uma casa decimal/);
});

test("conclusão produz dados do contrato e valida relatos declarados", () => {
  const form = cases.casos[0].entrada;
  const { condicoes_saude, medicamentos, limitacoes, observacoes, ...withoutDefaults } = form;
  expect(prepareForm(withoutDefaults, true)).toEqual({ ...withoutDefaults, condicoes_saude, medicamentos, limitacoes, observacoes });
  expect(() => prepareForm({ ...form, possui_dor_lesao_limitacao: "SIM" }, true)).toThrow(/Adicione/);
  expect(() => prepareForm({ ...form, possui_dor_lesao_limitacao: "SIM", limitacoes: [{}] }, true)).toThrow(/Região/);
  expect(prepareForm({ ...form, usa_medicamentos: "NAO_SEI", medicamentos: [{ nome: "Item removido" }] }, true))
    .toEqual({ ...form, usa_medicamentos: "NAO_SEI", medicamentos: [] });
});

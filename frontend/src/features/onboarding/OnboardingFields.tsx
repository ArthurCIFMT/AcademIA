import { useId } from "react";

import { healthGroups, otherHealthFields, profileFields, type Field, type FormData } from "./form";

function FieldControl({ field, value, onChange }: {
  field: Field;
  value: string | number | null | undefined;
  onChange?: (value: string | null) => void;
}) {
  const id = useId();
  if (!onChange) {
    const display = field.kind === "choice" ? field.options.find(([key]) => key === value)?.[1] : value;
    return <div className="onboarding-field"><dt>{field.label}</dt><dd>{display === 0 ? 0 : display || "Não informado"}</dd></div>;
  }
  const change = (value: string) => onChange(value === "" && field.kind !== "notes" ? null : value);
  return (
    <div className="onboarding-field">
      <label htmlFor={id}>{field.label}</label>
      {field.kind === "choice" ? (
        <select id={id} value={value ?? ""} onChange={(event) => change(event.target.value)}>
          <option value="">Selecione</option>
          {field.options.map(([key, label]) => <option key={key} value={key}>{label}</option>)}
        </select>
      ) : field.kind === "notes" ? (
        <textarea id={id} value={value ?? ""} maxLength={field.maxLength}
          onChange={(event) => change(event.target.value)} />
      ) : (
        <input id={id} value={value ?? ""} type={field.kind === "number" ? "number" : "text"}
          min={field.kind === "number" ? field.min : undefined}
          max={field.kind === "number" ? field.max : undefined}
          step={field.kind === "number" ? field.step : undefined}
          inputMode={field.kind === "number" ? field.step === 1 ? "numeric" : "decimal" : undefined}
          maxLength={field.kind === "text" ? field.maxLength : undefined}
          onChange={(event) => change(event.target.value)} />
      )}
    </div>
  );
}

export function OnboardingFields({ data, onChange }: {
  data: FormData;
  onChange?: (value: FormData) => void;
}) {
  const Fields = onChange ? "div" : "dl";
  return (
    <>
      <section>
        <h3>Dados físicos e rotina de treino</h3>
        <Fields className="onboarding-grid">
          {profileFields.map((field) => <FieldControl key={field.name} field={field} value={data[field.name]}
            onChange={onChange && ((value) => onChange({ ...data, [field.name]: value }))} />)}
        </Fields>
      </section>
      {healthGroups.map((group) => {
        const rows = data[group.list] ?? [];
        const show = data[group.answer.name] === "SIM";
        return (
          <section key={group.list}>
            <h3>{group.label}</h3>
            <Fields className="onboarding-grid">
              <FieldControl field={group.answer} value={data[group.answer.name]}
                onChange={onChange && ((value) => onChange({ ...data, [group.answer.name]: value }))} />
            </Fields>
            {show && rows.map((row, index) => {
              const label = group.item + " " + (index + 1);
              return (
                <div className="onboarding-entry" key={index}>
                  <h4>{label}</h4>
                  <Fields className="onboarding-grid">
                    {group.fields.map((field) => <FieldControl key={field.name} field={field}
                      value={row[field.name]} onChange={onChange && ((value) =>
                        onChange({ ...data, [group.list]: rows.map((entry, position) =>
                          position === index ? { ...entry, [field.name]: value } : entry) }))} />)}
                  </Fields>
                  {onChange && <button type="button" onClick={() =>
                    onChange({ ...data, [group.list]: rows.filter((_, position) => position !== index) })}>
                    Remover {label}
                  </button>}
                </div>
              );
            })}
            {onChange && show && <button type="button" disabled={rows.length >= group.max}
              onClick={() => onChange({ ...data, [group.list]: [...rows, {}] })}>Adicionar {group.item}</button>}
            {onChange && !show && rows.length > 0 &&
              <p>Ao salvar esta resposta, os registros desta seção serão removidos do rascunho.</p>}
          </section>
        );
      })}
      <section>
        <h3>Restrições e observações</h3>
        <Fields className="onboarding-grid">
          {otherHealthFields.map((field) => <FieldControl key={field.name} field={field} value={data[field.name]}
            onChange={onChange && ((value) => onChange({ ...data, [field.name]: value }))} />)}
        </Fields>
      </section>
    </>
  );
}

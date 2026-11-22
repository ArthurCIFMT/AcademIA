import { useId } from "react";

import { healthGroups, otherHealthFields, physicalFields, routineFields, type EditingStep, type Field, type FormData } from "./form";

function FieldControl({ field, value, onChange, name = field.name, invalidField }: {
  field: Field;
  value: string | number | null | undefined;
  onChange?: (value: string | null) => void;
  name?: string;
  invalidField?: string;
}) {
  const id = useId();
  if (!onChange) {
    const display = field.kind === "choice" ? field.options.find(([key]) => key === value)?.[1] : value;
    return <div className="onboarding-field"><dt>{field.label}</dt><dd>{display === 0 ? 0 : display || "Não informado"}</dd></div>;
  }
  const change = (value: string) => onChange(value === "" && field.kind !== "notes" ? null : value);
  const invalid = invalidField === name;
  const attributes = {
    id, name, value: value ?? "", "aria-invalid": invalid || undefined,
    "aria-describedby": invalid ? "onboarding-feedback" : undefined,
  };
  return (
    <div className="onboarding-field">
      <label htmlFor={id}>{field.label}</label>
      {field.kind === "choice" ? (
        <select {...attributes} onChange={(event) => change(event.target.value)}>
          <option value="">Selecione</option>
          {field.options.map(([key, label]) => <option key={key} value={key}>{label}</option>)}
        </select>
      ) : field.kind === "notes" ? (
        <textarea {...attributes} maxLength={field.maxLength}
          onChange={(event) => change(event.target.value)} />
      ) : (
        <input {...attributes} type={field.kind === "number" ? "number" : "text"}
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

export function OnboardingFields({ data, onChange, step, invalidField }: {
  data: FormData;
  onChange?: (value: FormData) => void;
  step?: EditingStep;
  invalidField?: string;
}) {
  const Fields = onChange ? "div" : "dl";
  return (
    <>
      {(!step || step !== "saude") && <section>
        {!step && <h3>Dados físicos e rotina de treino</h3>}
        <Fields className="onboarding-grid">
          {(step === "rotina" ? routineFields : step === "fisico" ? physicalFields : [...routineFields, ...physicalFields])
            .map((field) => <FieldControl key={field.name} field={field} value={data[field.name]} invalidField={invalidField}
            onChange={onChange && ((value) => onChange({ ...data, [field.name]: value }))} />)}
        </Fields>
      </section>}
      {(!step || step === "saude") && healthGroups.map((group) => {
        const rows = data[group.list] ?? [];
        const show = data[group.answer.name] === "SIM";
        return (
          <section key={group.list}>
            <h3>{group.label}</h3>
            <Fields className="onboarding-grid">
              <FieldControl field={group.answer} value={data[group.answer.name]} invalidField={invalidField}
                onChange={onChange && ((value) => onChange({ ...data, [group.answer.name]: value }))} />
            </Fields>
            {show && rows.map((row, index) => {
              const label = group.item + " " + (index + 1);
              return (
                <div className="onboarding-entry" key={index}>
                  <h4>{label}</h4>
                  <Fields className="onboarding-grid">
                    {group.fields.map((field) => <FieldControl key={field.name} field={field}
                      name={`${group.list}.${index}.${field.name}`} invalidField={invalidField}
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
            {onChange && show && <button type="button" name={group.list} disabled={rows.length >= group.max}
              aria-describedby={invalidField === group.list ? "onboarding-feedback" : undefined}
              onClick={() => onChange({ ...data, [group.list]: [...rows, {}] })}>Adicionar {group.item}</button>}
            {onChange && !show && rows.length > 0 &&
              <p>Ao salvar esta resposta, os registros desta seção serão removidos do rascunho.</p>}
          </section>
        );
      })}
      {(!step || step === "saude") && <section>
        <h3>Restrições e observações</h3>
        <Fields className="onboarding-grid">
          {otherHealthFields.map((field) => <FieldControl key={field.name} field={field} value={data[field.name]} invalidField={invalidField}
            onChange={onChange && ((value) => onChange({ ...data, [field.name]: value }))} />)}
        </Fields>
      </section>}
    </>
  );
}

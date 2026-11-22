import { useEffect, useRef } from "react";

import { Button, StatusMessage } from "../../ui/primitives";
import type { OpinionState, Workout } from "./api";

export const opinions: Record<OpinionState, string> = {
  PENDENTE: "Pendente", ACEITO: "Aceito", REJEITADO: "Rejeitado",
};
export const publicationDate = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "short", timeStyle: "short", timeZone: "America/Sao_Paulo",
});
const weight = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function Equipment({ equipment, withoutEquipment }: {
  equipment: Array<Workout["equipamentos"][number] | undefined>; withoutEquipment: boolean;
}) {
  return <div className="my-training-resources">
    <strong>Equipamentos</strong>
    {equipment.length === 0
      ? <p>{withoutEquipment ? "Dispensa equipamento" : "Recursos não informados"}</p>
      : <ul>{equipment.map((entry, index) => <li key={index}>
        {entry?.nome ?? "Equipamento não encontrado"}{!entry?.disponivel && " · Indisponível"}
      </li>)}</ul>}
    {equipment.some(entry => !entry?.disponivel) && <p role="note" className="my-training-warning">
      Há equipamento indisponível neste exercício. Consulte seu instrutor.
    </p>}
  </div>;
}

export function Prescription({ workout, selectedDay, onSelectDay }: {
  workout: Workout;
  selectedDay: number;
  onSelectDay: (index: number) => void;
}) {
  const { ficha, parecer } = workout;
  const day = ficha.dias[selectedDay];
  const dayHeading = useRef<HTMLHeadingElement>(null);
  const moveFocus = useRef(false);
  const resources = new Map(workout.equipamentos.map(item => [item.id, item]));
  useEffect(() => {
    if (moveFocus.current) {
      moveFocus.current = false;
      dayHeading.current?.focus();
    }
  }, [selectedDay]);

  return <article aria-label={"Ficha da versão " + ficha.numero} className="my-training-prescription">
    <div className="my-training-summary">
      <p>{ficha.origem === "MANUAL" ? "Ficha manual" : "Ficha gerada por IA"} · Publicada em {publicationDate.format(new Date(ficha.publicada_em))}</p>
      <span className="my-training-opinion" data-state={parecer.estado}>Parecer do instrutor · {opinions[parecer.estado]}</span>
      <details className="my-training-details">
        <summary>Detalhes do parecer e da autoria</summary>
        {parecer.estado === "PENDENTE" && <p>Você pode consultar esta ficha enquanto aguarda o parecer.</p>}
        {parecer.estado === "REJEITADO" && <p>A ficha continua disponível para consulta mesmo após a rejeição.</p>}
        {parecer.estado !== "REJEITADO" && parecer.motivo && <p>Motivo · {parecer.motivo}</p>}
        {parecer.instrutor_id && <p>Responsável pelo parecer · {parecer.instrutor_id}</p>}
        {parecer.criado_em && <p>Registrado em {publicationDate.format(new Date(parecer.criado_em))}</p>}
        {ficha.autor_id && <p>Identificação do autor · {ficha.autor_id}</p>}
      </details>
      {parecer.estado === "REJEITADO" && parecer.motivo && <p className="my-training-review-reason">Motivo · {parecer.motivo}</p>}
    </div>
    {day ? <>
      <nav aria-label="Dias da ficha">
        <ul className="my-training-days">{ficha.dias.map((entry, index) => <li key={index}>
          <Button variant={index === selectedDay ? "primary" : "secondary"}
            aria-current={index === selectedDay ? "step" : undefined} aria-controls="my-training-day"
            onClick={() => {
              if (selectedDay === index) dayHeading.current?.focus();
              else {
                moveFocus.current = true;
                onSelectDay(index);
              }
            }}>{entry.titulo}</Button>
        </li>)}</ul>
      </nav>
      <section id="my-training-day" aria-labelledby="my-training-day-title">
        <h4 id="my-training-day-title" ref={dayHeading} tabIndex={-1}>{day.titulo}</h4>
        {day.itens.length === 0 ? <p>Este dia não tem exercícios registrados.</p> :
          <ol className="my-training-items">{day.itens.map((item, index) => <li key={index} className="my-training-item">
            <h5>{item.exercicio_snapshot.nome}</h5>
            {item.exercicio_snapshot.descricao && <p>{item.exercicio_snapshot.descricao}</p>}
            <dl className="my-training-values">
              <div><dt>Séries</dt><dd>{item.series}</dd></div>
              <div><dt>Repetições</dt><dd>{item.repeticoes}</dd></div>
              <div><dt>Descanso</dt><dd>{item.intervalo_segundos} segundos</dd></div>
              <div><dt>Carga</dt><dd>{item.carga_kg === null ? "Não informada" : weight.format(Number(item.carga_kg)) + " kg"}</dd></div>
              <div><dt>Cadência</dt><dd>{item.cadencia ?? "Não informada"}</dd></div>
            </dl>
            <Equipment equipment={item.equipamento_ids.map(id => resources.get(id))}
              withoutEquipment={item.exercicio_snapshot.dispensa_equipamento} />
            {item.observacoes && <p className="my-training-observation">Observações · {item.observacoes}</p>}
          </li>)}</ol>}
        <p className="my-training-muted">Disponibilidade dos equipamentos consultada em {publicationDate.format(new Date(workout.consultado_em))}.</p>
      </section>
    </> : <StatusMessage state="empty" title="Esta ficha não tem dias registrados." />}
  </article>;
}

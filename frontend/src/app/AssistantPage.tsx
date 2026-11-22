import { Link, useLocation, useSearchParams } from "react-router-dom";

import { AITrainingPage } from "../features/ai-training/AITraining";
import { TrainingChatPage } from "../features/training-chat/TrainingChat";
import { paths } from "./areaNavigation";

export function AssistantPage({ csrf }: { csrf: string }) {
  const { pathname, search } = useLocation();
  const [params] = useSearchParams();
  const generating = pathname.replace(/\/+$/, "").toLowerCase() === paths.clientGeneration;
  const adapting = !generating && params.get("modo") === "adaptacao";
  const action = generating ? "generation" : adapting ? "adaptation" : "question";
  const actions = [
    { id: "question", to: paths.clientAssistant, label: "Tirar dúvida" },
    { id: "generation", to: paths.clientGeneration, label: "Gerar ficha" },
    { id: "adaptation", to: paths.clientAssistant + "?modo=adaptacao", label: "Adaptar um dia" },
  ];
  return (
    <section className="assistant">
      <h2>Assistente de treino</h2>
      <nav aria-label="Ações do assistente">
        <ul className="assistant-actions">
          {actions.map(item => <li key={item.id}>
            <Link to={action === item.id ? { pathname, search } : item.to}
              aria-current={action === item.id ? "page" : undefined}>{item.label}</Link>
          </li>)}
        </ul>
      </nav>
      {generating ? <AITrainingPage csrf={csrf} /> :
        <TrainingChatPage key={action} csrf={csrf} mode={adapting ? "ADAPTACAO" : "DUVIDA"} />}
    </section>
  );
}

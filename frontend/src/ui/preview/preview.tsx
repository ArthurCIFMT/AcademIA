import { type FormEvent, useState } from "react";
import { createRoot } from "react-dom/client";
import { Button, Card, FormField, NavigationDisclosure, ResponsiveTable, StatusMessage } from "../primitives";
import "../../styles.css";
import "./preview.css";

function ExampleForm() {
  const [email, setEmail] = useState("");
  const [result, setResult] = useState<"empty" | "invalid" | "valid">("empty");
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const input = event.currentTarget.elements.namedItem("email") as HTMLInputElement;
    setResult(input.validity.valid ? "valid" : "invalid");
    if (!input.validity.valid) input.focus();
  }
  return (
    <Card title="Formulário de exemplo">
      <form className="preview-stack" noValidate onSubmit={submit}>
        <FormField label="E-mail" hint="Exemplo: cliente@example.test" required
          error={result === "invalid" ? "Informe um e-mail válido." : undefined}>
          {control => <input {...control} name="email" type="email" value={email}
            onChange={event => { setEmail(event.target.value); setResult("empty"); }} />}
        </FormField>
        <div className="preview-actions">
          <Button type="submit">Validar exemplo</Button>
          <Button variant="secondary" onClick={() => { setEmail(""); setResult("empty"); }}>Limpar</Button>
        </div>
        {result === "valid" && <StatusMessage state="success" title="E-mail válido">Exemplo conferido neste navegador.</StatusMessage>}
      </form>
    </Card>
  );
}

function ExampleTable() {
  return (
    <Card title="Tabela com rolagem local">
      <p id="tabela">Em telas estreitas, deslize na tabela para ler as demais colunas.</p>
      <ResponsiveTable caption="Equipamentos de exemplo">
        <thead><tr><th scope="col">Equipamento</th><th scope="col">Disponibilidade</th><th scope="col">Última revisão</th><th scope="col">Área responsável</th></tr></thead>
        <tbody>
          <tr><th scope="row">Halteres</th><td>Disponíveis</td><td>12/11/2026</td><td>Administração</td></tr>
          <tr><th scope="row">Banco regulável</th><td>Indisponível</td><td>12/11/2026</td><td>Administração</td></tr>
        </tbody>
      </ResponsiveTable>
    </Card>
  );
}

function Preview() {
  return (
    <main className="shell ac-ui preview">
      <header className="preview-header">
        <p>AcademIA · Componentes UX-02</p>
        <h1>Base visual da interface</h1>
        <p>Demonstração local com dados sintéticos.</p>
      </header>
      <NavigationDisclosure label="Ir para um exemplo" navigationLabel="Exemplos disponíveis">
        <a href="#formulario">Formulário</a> · <a href="#tabela">Tabela</a>
      </NavigationDisclosure>
      <div className="preview-columns">
        <div className="preview-stack" id="formulario">
          <ExampleForm />
          <ExampleTable />
        </div>
        <div className="preview-stack">
          <Card title="Estados do sistema">
            <div className="preview-stack">
              <StatusMessage state="empty" title="Sem registros">Seu primeiro registro aparecerá aqui.</StatusMessage>
              <StatusMessage state="loading" title="Carregando">Buscando os dados.</StatusMessage>
              <StatusMessage state="conflict" title="Versão alterada">Recarregue para conferir a revisão mais recente.</StatusMessage>
              <StatusMessage state="error" title="Falha de conexão">Confira a conexão e tente novamente.</StatusMessage>
              <Button pending pendingLabel="Salvando…">Salvar</Button>
              <Button disabled>Publicação indisponível</Button>
            </div>
          </Card>
        </div>
      </div>
    </main>
  );
}

const root = document.getElementById("root");
if (!root) throw new Error("Elemento raiz indisponível.");
createRoot(root).render(<Preview />);

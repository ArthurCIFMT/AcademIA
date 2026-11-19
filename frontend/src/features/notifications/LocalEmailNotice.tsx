export function LocalEmailNotice() {
  const configured = import.meta.env.VITE_TEST_MAILBOX_URL?.trim();
  let mailbox: string | undefined;
  if (configured) {
    try {
      const url = new URL(configured);
      if (url.protocol === "http:" && ["127.0.0.1", "localhost", "[::1]"].includes(url.hostname)
          && !url.username && !url.password) mailbox = url.href;
    } catch {
      // A orientação continua disponível quando o endereço local não é válido.
    }
  }
  return (
    <p role="note">
      Ambiente acadêmico local: os e-mails ficam na caixa de testes Mailpit.
      Eles não são enviados ao Gmail, Outlook ou outros provedores.{" "}
      {mailbox && <a href={mailbox} target="_blank" rel="noopener noreferrer">Abrir caixa de e-mails de teste</a>}
    </p>
  );
}

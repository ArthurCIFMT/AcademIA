import sys
from datetime import date
from getpass import getpass

from pydantic import SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import create_database_engine, create_session_factory
from app.modules.identity.bootstrap import bootstrap_admin
from app.modules.identity.passwords import Passwords
from app.modules.identity.service import utc_now


class BootstrapSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ACADEMIA_BOOTSTRAP_", hide_input_in_errors=True
    )

    email: str
    nome: str
    data_admissao: date
    senha: SecretStr | None = None


def main() -> int:
    try:
        settings = BootstrapSettings()
    except ValidationError:
        print(
            "Configure e-mail, nome e data de admissão do bootstrap.", file=sys.stderr
        )
        return 1

    if settings.senha is None and not sys.stdin.isatty():
        print("Use um terminal ou forneça a senha pelo ambiente.", file=sys.stderr)
        return 1

    try:
        password = (
            settings.senha.get_secret_value()
            if settings.senha is not None
            else getpass("Senha do administrador: ")
        )
        engine = create_database_engine("dev")
        try:
            sessions = create_session_factory(engine)
            with sessions.begin() as session:
                bootstrap_admin(
                    session,
                    email=settings.email,
                    name=settings.nome,
                    hired_on=settings.data_admissao,
                    password=password,
                    passwords=Passwords(),
                    now=utc_now(),
                )
        finally:
            engine.dispose()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("Bootstrap cancelado.", file=sys.stderr)
        return 1
    except SQLAlchemyError:
        print(
            "Falha no PostgreSQL. Verifique a conexão e as migrations.", file=sys.stderr
        )
        return 1

    print("Administrador inicial disponível.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

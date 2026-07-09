"""CLI officielle Urban Cyber Architect."""

from __future__ import annotations

import argparse
import asyncio
import getpass
import sys

from app.database import async_session, engine
from app.models import Base, register_all_models
from app.services.admin.bootstrap_admin_service import bootstrap_admin_cli


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    bootstrap = sub.add_parser(
        "bootstrap-admin",
        help="Créer ou réinitialiser un compte administrateur",
    )
    bootstrap.add_argument("--username", default="admin", help="Login administrateur")
    bootstrap.add_argument("--password", help="Mot de passe (sinon invite sécurisée)")
    bootstrap.add_argument("--first-name", dest="first_name", default="Super")
    bootstrap.add_argument("--last-name", dest="last_name", default="Administrateur")
    bootstrap.add_argument("--email", default=None)
    bootstrap.add_argument(
        "--reset",
        action="store_true",
        help="Réinitialiser le mot de passe si le compte existe déjà",
    )
    return parser


async def _run_bootstrap(args: argparse.Namespace) -> int:
    password = args.password or getpass.getpass("Mot de passe administrateur : ")
    if not password:
        print("Mot de passe requis.", file=sys.stderr)
        return 1
    confirm = args.password or getpass.getpass("Confirmer le mot de passe : ")
    if password != confirm:
        print("Les mots de passe ne correspondent pas.", file=sys.stderr)
        return 1

    # La CLI peut être lancée avant tout démarrage de l'API : on garantit que le
    # schéma existe (idempotent) afin de fonctionner sur une base vierge.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        result = await bootstrap_admin_cli(
            session,
            username=args.username,
            password=password,
            first_name=args.first_name,
            last_name=args.last_name,
            email=args.email,
            reset=args.reset,
        )
    action = "créé" if result["action"] == "created" else "réinitialisé"
    print(f"Administrateur {action} : {result['username']} (rôle {result['role']})")
    return 0


def main(argv: list[str] | None = None) -> int:
    register_all_models()
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "bootstrap-admin":
        return asyncio.run(_run_bootstrap(args))
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

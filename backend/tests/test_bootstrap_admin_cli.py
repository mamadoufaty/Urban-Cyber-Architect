"""Régression — la CLI ``bootstrap-admin`` doit fonctionner sur une base vide.

Le bug d'origine : la CLI ne chargeait que les modèles Administration, si bien
que ``configure_mappers()`` échouait avec
``expression 'Project' failed to locate a name ('Project')`` dès la première
requête. On vérifie ici que :

* tous les modèles sont enregistrés dès l'import de ``app.models`` ;
* la CLI complète s'exécute sans erreur de mapper dans un interpréteur neuf
  (sous-processus), ce qui reproduit fidèlement le contexte d'origine.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401 — enregistre l'intégralité des modèles
from app.models import Base, register_all_models
from app.models.admin import User
from app.services.admin.bootstrap_admin_service import bootstrap_admin_cli

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_all_models_registered_before_configure_mappers():
    """Tous les mappers (dont Project) se configurent sans erreur."""
    register_all_models()

    registered = {mapper.class_.__name__ for mapper in Base.registry.mappers}
    assert "Project" in registered
    assert "User" in registered
    assert "Organization" in registered


@pytest_asyncio.fixture
async def empty_db_session() -> AsyncSession:
    """Base *vide* : schéma créé, aucune donnée (pas même le seed)."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_bootstrap_admin_cli_on_empty_database(empty_db_session: AsyncSession):
    """bootstrap-admin crée l'admin et amorce le seed sur une base vierge.

    On utilise un login absent de ``DEMO_USERS`` pour exercer le chemin de
    *création* (le seed provisionne déjà un compte ``admin``).
    """
    outcome = await bootstrap_admin_cli(
        empty_db_session,
        username="cli_admin",
        password="Admin@123",
    )

    assert outcome["action"] == "created"
    assert outcome["username"] == "cli_admin"

    result = await empty_db_session.execute(select(User).where(User.username == "cli_admin"))
    user = result.scalar_one()
    assert user.role_id is not None

    # Le compte 'admin' fourni par le seed doit également exister sur base vierge.
    seeded = await empty_db_session.execute(select(User).where(User.username == "admin"))
    assert seeded.scalar_one_or_none() is not None


def test_bootstrap_admin_cli_subprocess(tmp_path: Path):
    """Exécute réellement ``python -m app.cli bootstrap-admin`` (interpréteur neuf).

    C'est le garde-fou principal contre la régression du mapper : le
    sous-processus part d'un registry SQLAlchemy vierge, exactement comme en
    production.
    """
    db_path = tmp_path / "empty.db"
    database_url = f"sqlite+aiosqlite:///{db_path.as_posix()}"

    # Crée le schéma d'une base vierge (équivalent d'une migration initiale).
    _create_schema(database_url)

    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(BACKEND_ROOT), env.get("PYTHONPATH", "")])
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.cli",
            "bootstrap-admin",
            "--username",
            "admin",
            "--password",
            "Admin@123",
        ],
        cwd=str(BACKEND_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r}\nstderr={completed.stderr!r}"
    )
    assert "failed to locate a name" not in completed.stderr
    assert "Administrateur" in completed.stdout


def _create_schema(database_url: str) -> None:
    """Crée le schéma via un interpréteur dédié (base de données vide)."""
    script = (
        "import asyncio\n"
        "from sqlalchemy.ext.asyncio import create_async_engine\n"
        "import app.models\n"
        "from app.models import Base\n"
        f"engine = create_async_engine({database_url!r})\n"
        "async def _run():\n"
        "    async with engine.begin() as conn:\n"
        "        await conn.run_sync(Base.metadata.create_all)\n"
        "    await engine.dispose()\n"
        "asyncio.run(_run())\n"
    )
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(BACKEND_ROOT), env.get("PYTHONPATH", "")])
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(BACKEND_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, (
        f"schéma non créé\nstdout={completed.stdout!r}\nstderr={completed.stderr!r}"
    )

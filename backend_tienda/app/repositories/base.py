"""Repository base classes and utilities."""

from __future__ import annotations

from typing import Iterable, Type, TypeVar

from sqlalchemy.orm import Session


ModelType = TypeVar("ModelType")


class Repository:
    """Base repository providing convenient access to the SQLAlchemy session."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, instance: ModelType) -> ModelType:
        self.session.add(instance)
        return instance

    def add_all(self, instances: Iterable[ModelType]) -> None:
        self.session.add_all(list(instances))

    def flush(self) -> None:
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def refresh(self, instance: ModelType) -> ModelType:
        self.session.refresh(instance)
        return instance

    def expunge(self, instance: ModelType) -> None:
        self.session.expunge(instance)

    def delete(self, instance: ModelType) -> None:
        self.session.delete(instance)

    def close(self) -> None:
        self.session.close()


def acquire(session: Session, repo_cls: Type["Repository"]) -> "Repository":
    """Helper to instantiate repositories via dependency injection."""

    return repo_cls(session)

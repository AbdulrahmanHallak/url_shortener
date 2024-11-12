from sqlalchemy.orm import Session

from . import schemas
from . import models


def get_url(db: Session, url_key: str) -> models.Url:
    return (
        db.query(models.Url)
        .filter(models.Url.key == url_key, models.Url.is_active)
        .first()
    )


def get_url_by_secret(db: Session, secret_key: str) -> models.Url:
    return (
        db.query(models.Url)
        .filter(models.Url.secret_key == secret_key, models.Url.is_active)
        .first()
    )


def create(db: Session, key: str, secret_key: str, target_url: str) -> models.Url:
    db_url = models.Url(target_url=target_url, key=key, secret_key=secret_key)
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    return db_url


def update_url_clicks(db: Session, db_url: schemas.Url) -> models.Url:
    db_url.clicks += 1
    db.commit()
    db.refresh(db_url)
    return db_url  # type: ignore


def deactivate_url(db: Session, secret_key: str) -> models.Url:
    db_url = get_url_by_secret(db, secret_key)
    if db_url:
        db_url.is_active = False  # type: ignore
        db.commit()
        db.refresh(db_url)
    return db_url

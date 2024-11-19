import validators
from fastapi.responses import RedirectResponse
from fastapi import FastAPI, HTTPException, status, Depends, Request

from shortener_app.config import get_settings
from . import schemas, models, repo
from starlette.datastructures import URL
from sqlalchemy.orm import Session
from .db import SessionLocal, engine
from shortener_app import keygen


app = FastAPI()
models.Base.metadata.create_all(
    bind=engine
)  # this creates the bd if does not already exist


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_admin_info(db_url: models.Url) -> schemas.UrlInfo:
    base_url = URL(get_settings().base_url)
    admin_endpoint = app.url_path_for(
        "administrator info", secret_key=db_url.secret_key
    )

    db_url.url = str(base_url.replace(path=db_url.key))
    db_url.admin_url = str(base_url.replace(path=admin_endpoint))
    return db_url


@app.get("/", status_code=status.HTTP_418_IM_A_TEAPOT)
def get_root():
    return ":)"


@app.post("/url", response_model=schemas.UrlInfo)
def create_url(
    url: schemas.UrlBase,
    db: Session = Depends(get_db),
):
    if not validators.url(url.target_url):
        raise HTTPException(status_code=400, detail="invalid url")

    # ensure key uniqueness
    key = keygen.generate_key()
    while repo.get_url(db, key):
        key = keygen.generate_key()
    secret_key = f"{key}_{keygen.generate_key(8)}"

    db_url = repo.create(db, key, secret_key, url.target_url)

    return get_admin_info(db_url)


@app.get("/{url_key}")
def forward_to_target_url(
    url_key: str, request: Request, db: Session = Depends(get_db)
):
    if db_url := repo.get_url(db, url_key):
        repo.update_url_clicks(db, db_url)
        return RedirectResponse(str(db_url.target_url))
    else:
        raise HTTPException(status_code=404, detail=f"Url {request.url} not found")


@app.get(
    "/admin/{secret_key}", name="administrator info", response_model=schemas.UrlInfo
)
def url_info(secret_key: str, request: Request, db: Session = Depends(get_db)):
    if url := repo.get_url_by_secret(db, secret_key):
        return get_admin_info(url)
    else:
        raise HTTPException(status_code=404, detail=f"Url {request.url} not found")


@app.delete("/admin/{secret_key}")
def delete_url(secret_key: str, request: Request, db: Session = Depends(get_db)):
    if db_url := repo.deactivate_url(db, secret_key=secret_key):
        message = f"Successfully deleted shortened URL for '{db_url.target_url}'"
        return {"detail": message}
    else:
        raise HTTPException(status_code=404, detail=f"Url {request.url} not found")


# TODO: Custom URL key: Let your users create custom URL keys instead of a random string.
# TODO: Peek URL: Create an endpoint for your users to check which target URL is behind a shortened URL.
# TODO: Graceful Forward: Check if the website exists before forwarding.

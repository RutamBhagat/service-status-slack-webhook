from fastapi import FastAPI, Response, status


def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    @app.head("/health", status_code=status.HTTP_200_OK, tags=["health"])
    async def health_check_head() -> Response:
        return Response(status_code=status.HTTP_200_OK)

    return app


app = create_app()


if __name__ == "__main__":
    print("Run with an ASGI server, e.g. `uvicorn main:app --reload`.")

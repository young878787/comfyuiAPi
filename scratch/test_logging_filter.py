import logging
import uvicorn
from fastapi import FastAPI

app = FastAPI()


class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "/api/status" not in record.getMessage()


@app.on_event("startup")
async def startup_event():
    logging.getLogger("uvicorn.access").addFilter(EndpointFilter())
    print("Filter added to uvicorn.access logger!")


@app.get("/api/status")
def status():
    return {"status": "ok"}


@app.get("/api/other")
def other():
    return {"status": "other"}


if __name__ == "__main__":
    print("Starting test server... Please query /api/status and /api/other to verify logs.")

    # Let's verify that adding filter works
    logger = logging.getLogger("uvicorn.access")
    logger.addFilter(EndpointFilter())

    # Simulate a log record
    record_status = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='127.0.0.1:4875 - "GET /api/status HTTP/1.1" 200 OK',
        args=(),
        exc_info=None,
    )
    record_other = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='127.0.0.1:4875 - "GET /api/other HTTP/1.1" 200 OK',
        args=(),
        exc_info=None,
    )

    assert not logger.filter(record_status), "Should filter status"
    assert logger.filter(record_other), "Should not filter other"
    print("Assertions passed! The filter works perfectly.")

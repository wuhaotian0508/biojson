from __future__ import annotations

from admin.app import app, admin_bp
from shared.settings import Settings

if __name__ == "__main__":
    settings = Settings.from_env()
    app.register_blueprint(admin_bp)
    app.run(host="0.0.0.0", port=settings.rag.admin_port if settings.rag else 5501, debug=settings.rag.debug if settings.rag else False)

from firebase_admin import App as FirebaseApp, initialize_app
from firebase_admin import credentials
from google.oauth2.service_account import Credentials

from dishka import provide, Provider, Scope

from corelib.cloud import CloudSettings


class FireBaseConfigsProvider(Provider):
    @provide(scope=Scope.APP)
    def get_cloud_settings(self) -> CloudSettings:
        return CloudSettings()

    @provide(scope=Scope.APP)
    def get_firebase_app(self, settings: CloudSettings) -> FirebaseApp:
        app = initialize_app(
            credentials.Certificate(settings.GOOGLE_APPLICATION_CREDENTIALS)
        )
        return app

    @provide(scope=Scope.APP)
    def get_google_creds(self, app: FirebaseApp) -> Credentials:
        return app.credential.get_credential()

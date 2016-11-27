import keyring
import threading

from keyrings.alt.file import EncryptedKeyring
from oauth2client.client import Credentials
from oauth2client.client import Storage as BaseStorage


KEY = "Aeshae2ohpho3engahm0iem9oowiet"


class SBKeyring(EncryptedKeyring):
    """
    Store password in the file and use hardcoded password to prevent application asking it from user
    """
    def _get_new_password(self):
        return KEY

    def _unlock(self):
        self.keyring_key = KEY


keyring.set_keyring(SBKeyring())


class Storage(BaseStorage):
    """Store and retrieve a single credential to and from the keyring.

    To use this module you must have the keyring module installed. See
    <http://pypi.python.org/pypi/keyring/>. This is an optional module and is
    not installed with oauth2client by default because it does not work on all
    the platforms that oauth2client supports, such as Google App Engine.

    The keyring module <http://pypi.python.org/pypi/keyring/> is a
    cross-platform library for access the keyring capabilities of the local
    system. The user will be prompted for their keyring password when this
    module is used, and the manner in which the user is prompted will vary per
    platform.

    Usage:
        s = Storage('name_of_application', 'user1')
        credentials = s.get()

    """

    def __init__(self, service_name, user_name):
        """
        Constructor.
        Args:
            service_name: string, The name of the service under which the
                          credentials are stored.
            user_name: string, The name of the user to store credentials for.
        """
        self._service_name = service_name
        self._user_name = user_name
        self._lock = threading.Lock()

    def acquire_lock(self):
        """
        Acquires any lock necessary to access this Storage.
        This lock is not reentrant.
        """
        self._lock.acquire()

    def release_lock(self):
        """
        Release the Storage lock.
        Trying to release a lock that isn't held will result in a
        RuntimeError.
        """
        self._lock.release()

    def locked_get(self):
        """Retrieve Credential from file.
        Returns:
            oauth2client.client.Credentials
        """
        credentials = None
        content = keyring.get_password(self._service_name, self._user_name)

        if content is not None:
            try:
                credentials = Credentials.new_from_json(content)
                credentials.set_store(self)
            except ValueError:
                pass

        return credentials

    def locked_put(self, credentials):
        """
        Write Credentials to file.
        Args:
            credentials: Credentials, the credentials to store.
        """
        keyring.set_password(self._service_name, self._user_name,
                             credentials.to_json())

    def locked_delete(self):
        """
        Delete Credentials file.
        Args:
            credentials: Credentials, the credentials to store.
        """
        keyring.set_password(self._service_name, self._user_name, '')

import httplib2
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
from oauth2client.keyring_storage import Storage


CLIENTSECRET_LOCATION = "./providers/client_secret.json"
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"

SCOPES = [
    "email",
    "profile",
    "https://www.googleapis.com/auth/blogger",
    "https://www.googleapis.com/auth/blogger.readonly",
    "https://picasaweb.google.com/data/",
]


def get_authorization_url(email_address, state=None):
    """
    Retrieve the authorization URL.
    """
    flow = flow_from_clientsecrets(CLIENTSECRET_LOCATION, ' '.join(SCOPES))
    flow.params['access_type'] = 'offline'
    flow.params['approval_prompt'] = 'force'
    flow.params['user_id'] = email_address
    flow.params['state'] = state
    return flow.step1_get_authorize_url(REDIRECT_URI)


def load_credentials(email):
    """
    Load credentials for user with email
    """
    storage = Storage("simpleblogger", email)
    return storage.get()


def save_credentials(credentials, email):
    """
    Save credentials in a file with email as key
    """
    storage = Storage("simpleblogger", email)
    storage.put(credentials)


def get_credentials(authorization_code):
    """
    Exchange an authorization code for OAuth 2.0 credentials
    """
    flow = flow_from_clientsecrets(CLIENTSECRET_LOCATION, ' '.join(SCOPES))
    flow.redirect_uri = REDIRECT_URI
    try:
        credentials = flow.step2_exchange(authorization_code)
    except FlowExchangeError:
        credentials = None
    return credentials


def get_user_info(credentials):
    """
    Send a request to the UserInfo API to retrieve the user's information.
    """
    user_info_service = build(
        serviceName='oauth2', version='v2',
        http=credentials.authorize(httplib2.Http()))
    user_info = None
    user_info = user_info_service.userinfo().get().execute()
    if user_info and user_info.get('id'):
        return user_info


def create_service(credentials, name, version='v3'):
    """
    Returns service object
    """
    http = httplib2.Http()
    http = credentials.authorize(http)
    return build(name, version, http=http)


def get_blogs(service, email):
    """
    Returns object with blogs suitable for storing
    """
    resource = service.blogs()
    response = resource.listByUser(userId="self").execute()
    blogs = []
    for item in response["items"]:
        blogs.append({
            "id": item["id"],
            "name": item["name"],
            "link": item["url"],
            "tags": [],
            "email": email
        })
    return blogs


def publish_post(blog, title, content, tags):
    """
    Publish post to the blog
    """
    credentials = load_credentials(blog["email"])
    service = create_service(credentials, "blogger")
    resource = service.posts()
    post = {
        "title": title,
        "content": content,
    }
    if tags != [u""]:
        post["labels"] = tags
    resource.insert(blogId=blog["id"], body=post).execute()

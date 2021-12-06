from pfunk.web.oauth2.models import AuthorizationCode, OAuth2Token, OAuth2Client
from pfunk.web.oauth2.indexes import AuthCodeByCode, TokenByAccessToken, TokenByRefreshToken


def publish_oauth2(project):
    """ Published all oauth2 functionalities 
    
    Args:
        project (`pfunk.project`):
            Project instance
    Returns:
        result (string):
            Result of the publish to faunadb
    """
    project.add_resources([AuthorizationCode, OAuth2Client, OAuth2Token])
    project.add_resources(
        [AuthCodeByCode, TokenByAccessToken, TokenByRefreshToken])
    return project.publish()

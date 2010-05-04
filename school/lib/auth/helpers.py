"""
Helpers for auth.

"""
from pylons import request

def signed_in():
    """
    Return signed in user or None.

    """
    identity = request.environ.get('repoze.who.identity', None)
    if identity is not None:
        return identity['user']
    else:
        return identity

from .views import get_version, create_user, auth_routes, get_all_users, get_user, patch_user

def setup_routes(app):
    # Auth
    app.router.add_routes(auth_routes)
    # Default
    app.router.add_get('/api/version', get_version)
    # User
    app.router.add_post('/api/v1/users', create_user)
    app.router.add_get('/api/v1/users', get_all_users)
    app.router.add_get('/api/v1/users/{user_id}', get_user)
    app.router.add_patch('/api/v1/users/{user_id}', patch_user)

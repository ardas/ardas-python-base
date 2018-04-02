import sqlalchemy as sa

meta = sa.MetaData()

SystemSettings = sa.Table(
    'system_settings', meta,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('name', sa.String, nullable=False, unique=True),
    sa.Column('value', sa.String, nullable=False)
)
User = sa.Table(
    'user', meta,
    sa.Column('user_id', sa.Integer, primary_key=True),
    sa.Column('login', sa.String, nullable=False, unique=True),
    sa.Column('password', sa.String, nullable=False),
    sa.Column('first_name', sa.String, nullable=True),
    sa.Column('last_name', sa.String, nullable=True),
    sa.Column('email', sa.String, nullable=False)
)

Permission = sa.Table(
    'permission', meta,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('user_id', sa.Integer, sa.ForeignKey('user.user_id', ondelete="CASCADE"), nullable=False),
    sa.Column('perm_name', sa.String, nullable=False)
)

_models = {
    'system_settings': SystemSettings,
    'user': User,
    'permission': Permission,
}


def get_model_by_name(name: str) -> sa.Table:
    return _models.get(name, None)

def row_to_dict(table: sa.Table, row: dict) -> dict:
    fields = table.columns.keys()
    data = {}
    for field in fields:
        if field == 'password':
            continue
        data[field] = row[field]
    return data
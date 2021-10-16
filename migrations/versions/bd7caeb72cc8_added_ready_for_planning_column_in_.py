"""added ready_for_planning column in Request

Revision ID: bd7caeb72cc8
Revises: 4d9e9849b0e3
Create Date: 2021-10-15 17:44:24.038430

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bd7caeb72cc8'
down_revision = '4d9e9849b0e3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('request', sa.Column('ready_for_planning', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('request', 'ready_for_planning')
    # ### end Alembic commands ###

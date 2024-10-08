"""Add healthcheck

Revision ID: 6578bc239f4f
Revises: ed53500906ba
Create Date: 2024-09-02 17:12:54.379140

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6578bc239f4f'
down_revision = 'ed53500906ba'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('healthcheck',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('last_hit', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('healthcheck')
    # ### end Alembic commands ###

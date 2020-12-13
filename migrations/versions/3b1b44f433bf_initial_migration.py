"""initial migration

Revision ID: 3b1b44f433bf
Revises: 
Create Date: 2020-12-13 05:21:19.591536

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b1b44f433bf'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('example_data',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('alias', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('example_data')
    # ### end Alembic commands ###

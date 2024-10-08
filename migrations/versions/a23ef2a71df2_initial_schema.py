"""initial_schema

Revision ID: a23ef2a71df2
Revises:
Create Date: 2024-09-22 21:57:23.470631

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a23ef2a71df2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('location', sa.String(), nullable=False),
        sa.Column('transformation_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'transformations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('image_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['image_id'],
            ['images.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'gray_scale_transformations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['id'],
            ['transformations.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'resize_transformations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.CheckConstraint('height <= 4096', name='height_lte_2160'),
        sa.CheckConstraint('height >= 1', name='height_gte_one'),
        sa.CheckConstraint('width <= 4096', name='width_lte_4096'),
        sa.CheckConstraint('width >= 1', name='width_gte_one'),
        sa.ForeignKeyConstraint(
            ['id'], ['transformations.id'], onupdate='CASCADE', ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'rotate_transformations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('angle', sa.Integer(), nullable=False),
        sa.CheckConstraint('angle <= 360', name='angle_lte_360'),
        sa.CheckConstraint('angle >= 1', name='angle_gte_one'),
        sa.ForeignKeyConstraint(
            ['id'],
            ['transformations.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('rotate_transformations')
    op.drop_table('resize_transformations')
    op.drop_table('gray_scale_transformations')
    op.drop_table('transformations')
    op.drop_table('users')
    op.drop_table('images')
    # ### end Alembic commands ###

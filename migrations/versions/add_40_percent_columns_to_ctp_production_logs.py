"""Menambahkan kolom 40_percent untuk semua warna pada tabel ctp_production_logs

Revision ID: add_40_percent_columns
Revises: 43cc4ce79ce4
Create Date: 2025-12-11 14:54:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_40_percent_columns'
down_revision = '43cc4ce79ce4'
branch_labels = None
depends_on = None


def upgrade():
    """Menambahkan kolom 40_percent untuk semua warna"""
    
    # Daftar warna yang akan ditambahkan kolom 40_percent
    colors = ['cyan', 'magenta', 'yellow', 'black', 'x', 'z', 'u', 'v', 'f', 'g', 'h', 'j']
    
    # Tambahkan kolom 40_percent untuk setiap warna
    for color in colors:
        column_name = f"{color}_40_percent"
        try:
            op.add_column('ctp_production_logs', sa.Column(column_name, sa.Float, nullable=True))
            print(f"Added column {column_name}")
        except Exception as e:
            print(f"Error adding column {column_name}: {e}")


def downgrade():
    """Menghapus kolom 40_percent untuk semua warna"""
    
    # Daftar warna yang akan dihapus kolom 40_percent-nya
    colors = ['cyan', 'magenta', 'yellow', 'black', 'x', 'z', 'u', 'v', 'f', 'g', 'h', 'j']
    
    # Hapus kolom 40_percent untuk setiap warna
    for color in colors:
        column_name = f"{color}_40_percent"
        try:
            op.drop_column('ctp_production_logs', column_name)
            print(f"Dropped column {column_name}")
        except Exception as e:
            print(f"Error dropping column {column_name}: {e}")
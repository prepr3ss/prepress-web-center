# Standard library imports
from datetime import datetime, time, timedelta
from functools import wraps
from io import BytesIO, StringIO
from urllib.parse import quote_plus
import calendar
import csv
import io
import locale
import logging
import os
import pytz
import random
import traceback

# Third party imports
from flask import Blueprint, abort, flash, jsonify, make_response, redirect, render_template, request, send_file, send_from_directory, session, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import String, and_, cast, extract, func, literal_column, or_, text
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import openpyxl
import pymysql

# Local imports
from config import DB_CONFIG
from models import db, Division, User, CTPProductionLog, PlateAdjustmentRequest, PlateBonRequest, KartuStockPlateFuji, KartuStockPlateSaphira, KartuStockChemicalFuji, KartuStockChemicalSaphira, MonthlyWorkHours, ChemicalBonCTP, BonPlate, CTPMachine, CTPProblemLog, CTPProblemPhoto, CTPProblemDocument, CTPNotification
from plate_mappings import PlateTypeMapping

# Timezone untuk Jakarta
jakarta_tz = pytz.timezone('Asia/Jakarta')
now_jakarta = datetime.now(jakarta_tz)

# Helper function to format datetime in Indonesian
def format_datetime_indonesia(dt):
    """Format datetime to Indonesian format"""
    if not dt:
        return ''
    
    bulan_indonesia = [
        'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ]
    
    day = dt.day
    month = bulan_indonesia[dt.month - 1]
    year = dt.year
    hour = str(dt.hour).zfill(2)
    minute = str(dt.minute).zfill(2)
    
    return f"{day} {month} {year} - {hour}:{minute}"

def format_tanggal_indonesia(dt):
    """Format date to Indonesian format"""
    if not dt:
        return ''
    
    bulan_indonesia = [
        'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ]
    
    day = dt.day
    month = bulan_indonesia[dt.month - 1]
    year = dt.year
    
    return f"{day} {month} {year}"

def require_ctp_access(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.can_access_ctp():
            flash('Akses ditolak. Anda tidak memiliki akses ke divisi CTP.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Create Blueprint for export routes
ctp_dashboard_bp = Blueprint('ctp_dashboard', __name__)

# Create logger for debugging
logger = logging.getLogger(__name__)

@ctp_dashboard_bp.route('/get-ctp-plate-usage')
@login_required
@require_ctp_access
def get_ctp_plate_usage():
    try:
        # Local imports to avoid global import edits

        # Read and validate inputs
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)

        if not year:
            year = datetime.now().year

        # Base filters
        filters = [extract('year', CTPProductionLog.log_date) == year]
        if month:
            filters.append(extract('month', CTPProductionLog.log_date) == month)

        # Build trend
        if month:
            granularity = 'daily'
            days = calendar.monthrange(year, month)[1]
            labels = [str(d) for d in range(1, days + 1)]
            totals = [0] * days
            goods = [0] * days
            not_goods = [0] * days

            rows = db.session.query(
                extract('day', CTPProductionLog.log_date).label('d'),
                func.coalesce(func.sum(CTPProductionLog.num_plate_good), 0).label('good'),
                func.coalesce(func.sum(CTPProductionLog.num_plate_not_good), 0).label('not_good')
            ).filter(
                *filters
            ).group_by(
                'd'
            ).order_by(
                'd'
            ).all()

            for d, g, ng in rows:
                idx = int(d) - 1
                g_val = int(g or 0)
                ng_val = int(ng or 0)
                goods[idx] = g_val
                not_goods[idx] = ng_val
                totals[idx] = g_val + ng_val
        else:
            granularity = 'monthly'
            labels = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
            totals = [0] * 12
            goods = [0] * 12
            not_goods = [0] * 12

            rows = db.session.query(
                extract('month', CTPProductionLog.log_date).label('m'),
                func.coalesce(func.sum(CTPProductionLog.num_plate_good), 0).label('good'),
                func.coalesce(func.sum(CTPProductionLog.num_plate_not_good), 0).label('not_good')
            ).filter(
                *filters
            ).group_by(
                'm'
            ).order_by(
                'm'
            ).all()

            for m, g, ng in rows:
                idx = int(m) - 1
                g_val = int(g or 0)
                ng_val = int(ng or 0)
                goods[idx] = g_val
                not_goods[idx] = ng_val
                totals[idx] = g_val + ng_val

        # Breakdown by plate type (plate_type_material)
        by_type_rows = db.session.query(
            CTPProductionLog.plate_type_material.label('type'),
            func.coalesce(func.sum(CTPProductionLog.num_plate_good), 0).label('good'),
            func.coalesce(func.sum(CTPProductionLog.num_plate_not_good), 0).label('not_good')
        ).filter(
            CTPProductionLog.plate_type_material.isnot(None),
            *filters
        ).group_by(
            CTPProductionLog.plate_type_material
        ).order_by(
            CTPProductionLog.plate_type_material
        ).all()

        by_type = []
        for t, g, ng in by_type_rows:
            t_label = (t or '').strip() or 'Lainnya'
            g_val = int(g or 0)
            ng_val = int(ng or 0)
            by_type.append({
                'type': t_label,
                'total': g_val + ng_val,
                'good': g_val,
                'not_good': ng_val
            })

        # Breakdown by group (ctp_group)
        by_group_rows = db.session.query(
            CTPProductionLog.ctp_group.label('group'),
            func.coalesce(func.sum(CTPProductionLog.num_plate_good), 0).label('good'),
            func.coalesce(func.sum(CTPProductionLog.num_plate_not_good), 0).label('not_good')
        ).filter(
            CTPProductionLog.ctp_group.isnot(None),
            *filters
        ).group_by(
            CTPProductionLog.ctp_group
        ).order_by(
            CTPProductionLog.ctp_group
        ).all()

        by_group = []
        for grp, g, ng in by_group_rows:
            grp_label = (grp or '').strip() or 'Lainnya'
            g_val = int(g or 0)
            ng_val = int(ng or 0)
            by_group.append({
                'group': grp_label,
                'total': g_val + ng_val,
                'good': g_val,
                'not_good': ng_val
            })

        return jsonify({
            'success': True,
            'scope': {'year': year, 'month': month if month else None},
            'trend': {
                'granularity': granularity,
                'labels': labels,
                'total': totals,
                'good': goods,
                'not_good': not_goods
            },
            'by_type': by_type,
            'by_group': by_group
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
@ctp_dashboard_bp.route('/get-ctp-plate-usage-by-type')
@login_required
@require_ctp_access
def get_ctp_plate_usage_by_type():
    try:

        # Inputs
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        if not year:
            year = datetime.now().year

        # Build filters and labels based on granularity
        filters = [extract('year', CTPProductionLog.log_date) == year]

        if month:
            filters.append(extract('month', CTPProductionLog.log_date) == month)
            days = calendar.monthrange(year, month)[1]
            labels = [str(d) for d in range(1, days + 1)]
            index_key = 'd'
            dim = extract('day', CTPProductionLog.log_date).label(index_key)
            granularity = 'daily'
        else:
            labels = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
            index_key = 'm'
            dim = extract('month', CTPProductionLog.log_date).label(index_key)
            granularity = 'monthly'

        # Query grouped by plate type and time bucket
        rows = db.session.query(
            CTPProductionLog.plate_type_material.label('type'),
            dim,
            func.coalesce(func.sum(CTPProductionLog.num_plate_good), 0).label('good'),
            func.coalesce(func.sum(CTPProductionLog.num_plate_not_good), 0).label('not_good')
        ).filter(
            CTPProductionLog.plate_type_material.isnot(None),
            *filters
        ).group_by(
            'type', index_key
        ).order_by(
            'type', index_key
        ).all()

        # Build series map
        length = len(labels)
        series_map = {}
        for t, idx_val, g, ng in rows:
            t_label = (t or '').strip() or 'Lainnya'
            if t_label not in series_map:
                series_map[t_label] = {
                    'type': t_label,
                    'good': [0] * length,
                    'not_good': [0] * length,
                    'total': [0] * length
                }
            try:
                i = int(idx_val) - 1
            except Exception:
                i = None
            if i is not None and 0 <= i < length:
                g_val = int(g or 0)
                ng_val = int(ng or 0)
                series_map[t_label]['good'][i] = g_val
                series_map[t_label]['not_good'][i] = ng_val
                series_map[t_label]['total'][i] = g_val + ng_val

        series = list(series_map.values())

        # Calculate average box usage
        # Define pieces per box mapping
        pieces_per_box = {
            'FUJI 1030': 30,
            'FUJI 1030 UV': 30,
            'FUJI 1030 LHPJA': 30,
            'FUJI 1055': 30,
            'FUJI 1055 UV': 30,
            'FUJI 1055 LHPL': 30,
            'FUJI 1630': 15,
            'SAPHIRA 1030': 50,
            'SAPHIRA 1055': 50,
            'SAPHIRA 1055 PN': 40,
            'SAPHIRA 1630': 30
        }

        # Calculate total usage per plate type for the entire period
        total_usage_by_type = {}
        for t_label, data in series_map.items():
            total_pieces = sum(data['total'])
            total_usage_by_type[t_label] = total_pieces

        # Calculate average box usage
        average_box_usage = []
        for plate_type, total_pieces in total_usage_by_type.items():
            pieces_per_box_value = pieces_per_box.get(plate_type, 30)  # Default to 30 if not found
            avg_boxes = total_pieces / pieces_per_box_value if pieces_per_box_value > 0 else 0
            average_box_usage.append({
                'plate_type': plate_type,
                'average_boxes': round(avg_boxes, 1)
            })

        return jsonify({
            'success': True,
            'scope': {'year': year, 'month': month if month else None},
            'granularity': granularity,
            'labels': labels,
            'series': series,
            'average_box_usage': average_box_usage
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ctp_dashboard_bp.route('/get-ctp-plate-usage-by-print-machine')
@login_required
@require_ctp_access
def get_ctp_plate_usage_by_print_machine():
    try:
        # Inputs
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        if not year:
            year = datetime.now().year

        # Build filters and labels based on granularity
        filters = [extract('year', CTPProductionLog.log_date) == year]

        if month:
            filters.append(extract('month', CTPProductionLog.log_date) == month)
            days = calendar.monthrange(year, month)[1]
            labels = [str(d) for d in range(1, days + 1)]
            index_key = 'd'
            dim = extract('day', CTPProductionLog.log_date).label(index_key)
            granularity = 'daily'
        else:
            labels = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
            index_key = 'm'
            dim = extract('month', CTPProductionLog.log_date).label(index_key)
            granularity = 'monthly'

        # Query grouped by print machine and time bucket
        rows = db.session.query(
            CTPProductionLog.print_machine.label('machine'),
            dim,
            func.coalesce(func.sum(CTPProductionLog.num_plate_good), 0).label('good'),
            func.coalesce(func.sum(CTPProductionLog.num_plate_not_good), 0).label('not_good')
        ).filter(
            CTPProductionLog.print_machine.isnot(None),
            *filters
        ).group_by(
            'machine', index_key
        ).order_by(
            'machine', index_key
        ).all()

        # Build series map
        length = len(labels)
        series_map = {}
        for machine, idx_val, g, ng in rows:
            machine_label = (machine or '').strip() or 'Tidak Diketahui'
            if machine_label not in series_map:
                series_map[machine_label] = {
                    'machine': machine_label,
                    'good': [0] * length,
                    'not_good': [0] * length,
                    'total': [0] * length
                }
            try:
                i = int(idx_val) - 1
            except Exception:
                i = None
            if i is not None and 0 <= i < length:
                g_val = int(g or 0)
                ng_val = int(ng or 0)
                series_map[machine_label]['good'][i] = g_val
                series_map[machine_label]['not_good'][i] = ng_val
                series_map[machine_label]['total'][i] = g_val + ng_val

        series = list(series_map.values())

        # Calculate total plates per machine for entire period
        total_plates_by_machine = {}
        for machine_label, data in series_map.items():
            total_pieces = sum(data['total'])
            total_plates_by_machine[machine_label] = total_pieces

        # Calculate average plates per machine
        average_plates = []
        for machine, total_pieces in total_plates_by_machine.items():
            average_plates.append({
                'machine': machine,
                'total_plates': total_pieces
            })

        return jsonify({
            'success': True,
            'scope': {'year': year, 'month': month if month else None},
            'granularity': granularity,
            'labels': labels,
            'series': series,
            'total_plates': average_plates
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
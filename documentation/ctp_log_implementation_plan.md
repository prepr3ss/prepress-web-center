# Implementation Plan: Log CTP System

## Overview
Dokumen ini berisi rencana implementasi lengkap untuk fitur Log CTP yang akan menampilkan status mesin CTP (CTP 1, CTP 2, CTP 3) dan mencatat problem yang terjadi beserta solusi dan perhitungan downtime.

## Database Design

### 1. Model CTPMachine
```python
class CTPMachine(db.Model):
    __tablename__ = 'ctp_machines'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # CTP 1 Suprasetter, CTP 2 Platesetter, CTP 3 Trendsetter
    nickname = db.Column(db.String(50), nullable=False)  # CTP 1, CTP 2, CTP 3
    status = db.Column(db.String(20), nullable=False, default='active')  # active, maintenance
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 2. Model CTPProblemLog
```python
class CTPProblemLog(db.Model):
    __tablename__ = 'ctp_problem_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('ctp_machines.id'), nullable=False)
    machine = db.relationship('CTPMachine', backref='problem_logs')
    
    # Informasi Problem
    problem_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    problem_description = db.Column(db.Text, nullable=False)
    problem_photo = db.Column(db.String(255), nullable=True)  # Path ke foto
    
    # Informasi Solusi
    solution = db.Column(db.Text, nullable=True)
    technician_type = db.Column(db.String(20), nullable=False)  # lokal, vendor
    technician_name = db.Column(db.String(100), nullable=True)
    
    # Waktu untuk perhitungan downtime
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    
    # Status
    status = db.Column(db.String(20), nullable=False, default='ongoing')  # ongoing, completed
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Property untuk menghitung downtime
    @property
    def downtime_hours(self):
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() / 3600  # Convert to hours
        elif self.status == 'ongoing':
            delta = datetime.utcnow() - self.start_time
            return delta.total_seconds() / 3600
        return 0
```

### 3. Model CTPNotification
```python
class CTPNotification(db.Model):
    __tablename__ = 'ctp_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('ctp_machines.id'), nullable=False)
    machine = db.relationship('CTPMachine', backref='notifications')
    
    log_id = db.Column(db.Integer, db.ForeignKey('ctp_problem_logs.id'), nullable=False)
    log = db.relationship('CTPProblemLog', backref='notifications')
    
    notification_type = db.Column(db.String(50), nullable=False)  # new_problem, problem_resolved
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
```

## Frontend Implementation

### 1. Sidebar Modification
File: `templates/_sidebar.html`

Tambahkan menu Log CTP di dalam CTP Production submenu:

```html
<!-- Setelah menu Kartu Stock CTP -->
<a href="#logCtpSubmenu" data-bs-toggle="collapse" aria-expanded="false"
   class="list-group-item list-group-item-action log-ctp-submenu-parent collapsed ps-4">
    <i class="fas fa-clipboard-list me-2"></i>
    <span>Log CTP</span>
    <i class="fas fa-chevron-right ms-auto"></i>
</a>
<div class="collapse" id="logCtpSubmenu">
    <a href="/impact/log-ctp" class="list-group-item list-group-item-action ps-5" id="logCtpOverviewLink">
        <i class="fas fa-dashboard me-2"></i>Overview
    </a>
    <a href="/impact/log-ctp/ctp-1" class="list-group-item list-group-item-action ps-5" id="logCtp1Link">
        <i class="fas fa-print me-2"></i>CTP 1 Suprasetter
    </a>
    <a href="/impact/log-ctp/ctp-2" class="list-group-item list-group-item-action ps-5" id="logCtp2Link">
        <i class="fas fa-print me-2"></i>CTP 2 Platesetter
    </a>
    <a href="/impact/log-ctp/ctp-3" class="list-group-item list-group-item-action ps-5" id="logCtp3Link">
        <i class="fas fa-print me-2"></i>CTP 3 Trendsetter
    </a>
</div>
```

### 2. Template HTML

#### a. Overview Page (`templates/log_ctp_overview.html`)
```html
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Log CTP - Impact 360</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="icon" type="image/x-icon" href="{{ url_for('static', filename='favicon.ico') }}">
    
    <style>
        .machine-card {
            border: none;
            border-radius: 15px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            background: white;
            cursor: pointer;
        }
        
        .machine-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .machine-status-active {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        }
        
        .machine-status-maintenance {
            background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
        }
        
        .breadcrumb-custom {
            background: linear-gradient(135deg, #ff9500 0%, #ff6b00 100%);
            color: white;
            padding: 1rem 0;
            margin: -1rem -15px 2rem -15px;
            border-radius: 0 0 20px 20px;
        }
    </style>
</head>
<body>
    <div class="d-flex" id="wrapper">
        {% include '_sidebar.html' %}
        <div id="page-content-wrapper">
            <div class="container-fluid">
                <!-- Breadcrumb -->
                <div class="breadcrumb-custom">
                    <div class="container-fluid">
                        <nav aria-label="breadcrumb">
                            <ol class="breadcrumb mb-0">
                                <li class="breadcrumb-item"><a href="/impact/" class="text-white text-decoration-none">Dashboard Impact</a></li>
                                <li class="breadcrumb-item"><a href="#" class="text-white text-decoration-none">Prepress Production</a></li>
                                <li class="breadcrumb-item"><a href="#" class="text-white text-decoration-none">CTP Production</a></li>
                                <li class="breadcrumb-item active text-white" aria-current="page">Log CTP</li>
                            </ol>
                        </nav>
                        <h2 class="mb-0 text-white mt-2">Log CTP - Overview</h2>
                    </div>
                </div>

                <!-- Machine Status Cards -->
                <div class="row" id="machineCards">
                    <!-- Cards will be dynamically inserted here -->
                </div>

                <!-- Recent Problems Section -->
                <div class="row mt-4">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">
                                <h5 class="card-title mb-0">
                                    <i class="fas fa-exclamation-triangle me-2"></i>Problem Terbaru
                                </h5>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-hover" id="recentProblemsTable">
                                        <thead>
                                            <tr>
                                                <th>Tanggal</th>
                                                <th>Mesin</th>
                                                <th>Problem</th>
                                                <th>Teknisi</th>
                                                <th>Status</th>
                                                <th>Downtime</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <!-- Data will be inserted here -->
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="{{ url_for('static', filename='js/log_ctp_handler.js') }}"></script>
</body>
</html>
```

#### b. Machine Detail Page (`templates/log_ctp_detail.html`)
```html
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Log CTP {{ machine_name }} - Impact 360</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="icon" type="image/x-icon" href="{{ url_for('static', filename='favicon.ico') }}">
    
    <style>
        .machine-header {
            background: linear-gradient(135deg, #ff9500 0%, #ff6b00 100%);
            color: white;
            padding: 2rem 0;
            margin: -1rem -15px 2rem -15px;
            border-radius: 0 0 20px 20px;
        }
        
        .status-badge {
            padding: 0.5rem 1rem;
            border-radius: 25px;
            font-weight: 600;
        }
        
        .status-active {
            background: rgba(40, 167, 69, 0.2);
            color: #28a745;
        }
        
        .status-maintenance {
            background: rgba(255, 193, 7, 0.2);
            color: #ffc107;
        }
        
        .problem-card {
            border-left: 4px solid #ff9500;
            transition: all 0.3s ease;
        }
        
        .problem-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .photo-preview {
            max-width: 100px;
            max-height: 100px;
            object-fit: cover;
            border-radius: 8px;
            cursor: pointer;
        }
        
        .downtime-calculator {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 1rem;
        }
    </style>
</head>
<body>
    <div class="d-flex" id="wrapper">
        {% include '_sidebar.html' %}
        <div id="page-content-wrapper">
            <div class="container-fluid">
                <!-- Machine Header -->
                <div class="machine-header">
                    <div class="container-fluid">
                        <nav aria-label="breadcrumb">
                            <ol class="breadcrumb mb-0">
                                <li class="breadcrumb-item"><a href="/impact/" class="text-white text-decoration-none">Dashboard Impact</a></li>
                                <li class="breadcrumb-item"><a href="#" class="text-white text-decoration-none">Prepress Production</a></li>
                                <li class="breadcrumb-item"><a href="#" class="text-white text-decoration-none">CTP Production</a></li>
                                <li class="breadcrumb-item"><a href="/impact/log-ctp" class="text-white text-decoration-none">Log CTP</a></li>
                                <li class="breadcrumb-item active text-white" aria-current="page">{{ machine_name }}</li>
                            </ol>
                        </nav>
                        <div class="d-flex justify-content-between align-items-center mt-3">
                            <div>
                                <h2 class="mb-1 text-white">{{ machine_name }}</h2>
                                <p class="mb-0 opacity-75">{{ machine_description }}</p>
                            </div>
                            <div class="text-end">
                                <span class="status-badge status-{{ machine_status }}" id="machineStatusBadge">
                                    {{ machine_status.upper() }}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="row mb-4">
                    <div class="col-12">
                        <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addProblemModal" id="btnAddProblem">
                            <i class="fas fa-plus-circle me-2"></i>Tambah Problem
                        </button>
                        <button class="btn btn-secondary" id="btnRefresh">
                            <i class="fas fa-sync-alt me-2"></i>Refresh
                        </button>
                    </div>
                </div>

                <!-- Statistics Cards -->
                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h5 class="card-title text-primary">Total Problem</h5>
                                <h2 class="text-primary" id="totalProblems">0</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h5 class="card-title text-warning">Problem Aktif</h5>
                                <h2 class="text-warning" id="activeProblems">0</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h5 class="card-title text-info">Total Downtime</h5>
                                <h2 class="text-info" id="totalDowntime">0 jam</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h5 class="card-title text-success">Rata-rata Downtime</h5>
                                <h2 class="text-success" id="avgDowntime">0 jam</h2>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Problems List -->
                <div class="row">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">
                                <div class="d-flex justify-content-between align-items-center">
                                    <h5 class="card-title mb-0">
                                        <i class="fas fa-list me-2"></i>Riwayat Problem
                                    </h5>
                                    <div class="d-flex gap-2">
                                        <input type="date" class="form-control" id="filterStartDate" placeholder="Tanggal Mulai">
                                        <input type="date" class="form-control" id="filterEndDate" placeholder="Tanggal Selesai">
                                        <select class="form-select" id="filterStatus">
                                            <option value="">Semua Status</option>
                                            <option value="ongoing">Sedang Berjalan</option>
                                            <option value="completed">Selesai</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-hover" id="problemsTable">
                                        <thead>
                                            <tr>
                                                <th>Tanggal</th>
                                                <th>Problem</th>
                                                <th>Solusi</th>
                                                <th>Teknisi</th>
                                                <th>Status</th>
                                                <th>Downtime</th>
                                                <th>Foto</th>
                                                <th>Aksi</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <!-- Data will be inserted here -->
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Add Problem Modal -->
    <div class="modal fade" id="addProblemModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">
                        <i class="fas fa-exclamation-triangle me-2"></i>Tambah Problem Baru
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="addProblemForm">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Tanggal Problem</label>
                                    <input type="datetime-local" class="form-control" id="problemDate" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Waktu Mulai</label>
                                    <input type="datetime-local" class="form-control" id="startTime" required>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Deskripsi Problem</label>
                            <textarea class="form-control" id="problemDescription" rows="3" required></textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Foto Problem</label>
                            <input type="file" class="form-control" id="problemPhoto" accept="image/*">
                            <div class="mt-2" id="photoPreview"></div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Jenis Teknisi</label>
                                    <select class="form-select" id="technicianType" required>
                                        <option value="">Pilih Jenis</option>
                                        <option value="lokal">Lokal</option>
                                        <option value="vendor">Vendor</option>
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Nama Teknisi</label>
                                    <input type="text" class="form-control" id="technicianName">
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Solusi</label>
                            <textarea class="form-control" id="solution" rows="3"></textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Waktu Selesai (kosongkan jika masih berjalan)</label>
                            <input type="datetime-local" class="form-control" id="endTime">
                        </div>
                        
                        <div class="downtime-calculator">
                            <h6>Perhitungan Downtime</h6>
                            <div class="row">
                                <div class="col-md-6">
                                    <small class="text-muted">Durasi:</small>
                                    <span id="downtimeCalculation">0 jam 0 menit</span>
                                </div>
                                <div class="col-md-6">
                                    <button type="button" class="btn btn-sm btn-outline-primary" id="btnCompleteProblem">
                                        <i class="fas fa-check me-1"></i>Selesai Sekarang
                                    </button>
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Batal</button>
                    <button type="button" class="btn btn-primary" id="btnSaveProblem">
                        <i class="fas fa-save me-1"></i>Simpan
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Photo Modal -->
    <div class="modal fade" id="photoModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Foto Problem</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body text-center">
                    <img id="modalPhoto" src="" alt="Foto Problem" class="img-fluid">
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="{{ url_for('static', filename='js/log_ctp_detail_handler.js') }}"></script>
</body>
</html>
```

## Backend Implementation

### 1. Routes di app.py

```python
# Log CTP Routes
@app.route('/log-ctp')
@login_required
def log_ctp_overview():
    if not (current_user.can_access_ctp() or current_user.role == 'admin'):
        flash('Anda tidak memiliki akses ke halaman ini', 'danger')
        return redirect(url_for('index'))
    
    # Get all machines with their status
    machines = CTPMachine.query.all()
    return render_template('log_ctp_overview.html', machines=machines)

@app.route('/log-ctp/<machine_nickname>')
@login_required
def log_ctp_detail(machine_nickname):
    if not (current_user.can_access_ctp() or current_user.role == 'admin'):
        flash('Anda tidak memiliki akses ke halaman ini', 'danger')
        return redirect(url_for('index'))
    
    # Get machine by nickname
    machine = CTPMachine.query.filter_by(nickname=machine_nickname).first()
    if not machine:
        flash('Mesin tidak ditemukan', 'danger')
        return redirect(url_for('log_ctp_overview'))
    
    return render_template('log_ctp_detail.html', 
                        machine=machine, 
                        machine_name=machine.name,
                        machine_description=machine.description,
                        machine_status=machine.status,
                        machine_nickname=machine.nickname)

# API Endpoints
@app.route('/api/ctp-machines', methods=['GET'])
@login_required
def get_ctp_machines():
    machines = CTPMachine.query.all()
    return jsonify({
        'success': True,
        'data': [{
            'id': m.id,
            'name': m.name,
            'nickname': m.nickname,
            'status': m.status,
            'description': m.description
        } for m in machines]
    })

@app.route('/api/ctp-problem-logs', methods=['GET'])
@login_required
def get_ctp_problem_logs():
    machine_id = request.args.get('machine_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status')
    
    query = CTPProblemLog.query
    
    if machine_id:
        query = query.filter_by(machine_id=machine_id)
    if start_date:
        query = query.filter(CTPProblemLog.problem_date >= start_date)
    if end_date:
        query = query.filter(CTPProblemLog.problem_date <= end_date)
    if status:
        query = query.filter_by(status=status)
    
    logs = query.order_by(CTPProblemLog.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'data': [{
            'id': log.id,
            'machine_id': log.machine_id,
            'machine_name': log.machine.name,
            'problem_date': log.problem_date.isoformat(),
            'problem_description': log.problem_description,
            'problem_photo': log.problem_photo,
            'solution': log.solution,
            'technician_type': log.technician_type,
            'technician_name': log.technician_name,
            'start_time': log.start_time.isoformat(),
            'end_time': log.end_time.isoformat() if log.end_time else None,
            'status': log.status,
            'downtime_hours': log.downtime_hours,
            'created_by': log.created_by,
            'created_at': log.created_at.isoformat()
        } for log in logs]
    })

@app.route('/api/ctp-problem-logs', methods=['POST'])
@login_required
def create_ctp_problem_log():
    if not (current_user.can_access_ctp() or current_user.role == 'admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Handle file upload
    photo_path = None
    if 'problem_photo' in request.files:
        file = request.files['problem_photo']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"ctp_problem_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            photo_path = filename
    
    # Create new problem log
    log = CTPProblemLog(
        machine_id=data['machine_id'],
        problem_description=data['problem_description'],
        problem_photo=photo_path,
        technician_type=data['technician_type'],
        technician_name=data.get('technician_name'),
        start_time=datetime.fromisoformat(data['start_time']),
        end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
        status='completed' if data.get('end_time') else 'ongoing',
        solution=data.get('solution'),
        created_by=current_user.id
    )
    
    db.session.add(log)
    db.session.commit()
    
    # Create notification
    notification = CTPNotification(
        machine_id=data['machine_id'],
        log_id=log.id,
        notification_type='new_problem',
        message=f"Problem baru pada {log.machine.name}: {data['problem_description'][:50]}..."
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'success': True, 'data': {'id': log.id}})

@app.route('/api/ctp-problem-logs/<int:log_id>', methods=['PUT'])
@login_required
def update_ctp_problem_log(log_id):
    if not (current_user.can_access_ctp() or current_user.role == 'admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    log = CTPProblemLog.query.get_or_404(log_id)
    data = request.get_json()
    
    # Update fields
    if 'solution' in data:
        log.solution = data['solution']
    if 'technician_name' in data:
        log.technician_name = data['technician_name']
    if 'end_time' in data and data['end_time']:
        log.end_time = datetime.fromisoformat(data['end_time'])
        log.status = 'completed'
        
        # Create notification for completed problem
        notification = CTPNotification(
            machine_id=log.machine_id,
            log_id=log.id,
            notification_type='problem_resolved',
            message=f"Problem pada {log.machine.name} telah selesai"
        )
        db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/ctp-problem-logs/<int:log_id>', methods=['DELETE'])
@login_required
def delete_ctp_problem_log(log_id):
    if not (current_user.can_access_ctp() or current_user.role == 'admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    log = CTPProblemLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/ctp-notifications', methods=['GET'])
@login_required
def get_ctp_notifications():
    notifications = CTPNotification.query.filter_by(is_read=False).order_by(CTPNotification.created_at.desc()).limit(10).all()
    
    return jsonify({
        'success': True,
        'data': [{
            'id': n.id,
            'machine_name': n.machine.name,
            'message': n.message,
            'notification_type': n.notification_type,
            'created_at': n.created_at.isoformat()
        } for n in notifications]
    })

@app.route('/api/ctp-notifications/<int:notification_id>/read', methods=['PUT'])
@login_required
def mark_notification_read(notification_id):
    notification = CTPNotification.query.get_or_404(notification_id)
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})
```

### 2. JavaScript Handler

#### a. `static/js/log_ctp_handler.js`
```javascript
document.addEventListener('DOMContentLoaded', function() {
    loadMachineCards();
    loadRecentProblems();
});

function loadMachineCards() {
    fetch('/impact/api/ctp-machines')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const container = document.getElementById('machineCards');
                container.innerHTML = '';
                
                data.data.forEach(machine => {
                    const card = createMachineCard(machine);
                    container.innerHTML += card;
                });
            }
        })
        .catch(error => {
            console.error('Error loading machines:', error);
            showToast('Gagal memuat data mesin', 'danger');
        });
}

function createMachineCard(machine) {
    const statusClass = machine.status === 'active' ? 'machine-status-active' : 'machine-status-maintenance';
    const statusText = machine.status === 'active' ? 'AKTIF' : 'PERBAIKAN';
    const statusIcon = machine.status === 'active' ? 'fa-check-circle' : 'fa-wrench';
    
    return `
        <div class="col-md-4 mb-4">
            <div class="machine-card" onclick="window.location.href='/impact/log-ctp/${machine.nickname}'">
                <div class="card-body text-center">
                    <div class="${statusClass} text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-3" 
                         style="width: 80px; height: 80px;">
                        <i class="fas fa-print fa-2x"></i>
                    </div>
                    <h5 class="card-title">${machine.name}</h5>
                    <p class="card-text text-muted">${machine.description || ''}</p>
                    <div class="d-flex align-items-center justify-content-center">
                        <i class="fas ${statusIcon} me-2"></i>
                        <span class="fw-semibold">${statusText}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function loadRecentProblems() {
    fetch('/impact/api/ctp-problem-logs?limit=5')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tbody = document.querySelector('#recentProblemsTable tbody');
                tbody.innerHTML = '';
                
                data.data.forEach(log => {
                    const row = createProblemRow(log);
                    tbody.innerHTML += row;
                });
            }
        })
        .catch(error => {
            console.error('Error loading recent problems:', error);
        });
}

function createProblemRow(log) {
    const statusBadge = log.status === 'completed' 
        ? '<span class="badge bg-success">Selesai</span>'
        : '<span class="badge bg-warning">Berjalan</span>';
    
    const downtime = log.downtime_hours ? `${log.downtime_hours.toFixed(1)} jam` : '-';
    
    return `
        <tr>
            <td>${formatDate(log.problem_date)}</td>
            <td>${log.machine_name}</td>
            <td>${log.problem_description.substring(0, 50)}...</td>
            <td>${log.technician_name || '-'}</td>
            <td>${statusBadge}</td>
            <td>${downtime}</td>
        </tr>
    `;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}
```

#### b. `static/js/log_ctp_detail_handler.js`
```javascript
let currentMachineId = null;

document.addEventListener('DOMContentLoaded', function() {
    // Get machine ID from URL
    const pathParts = window.location.pathname.split('/');
    currentMachineId = pathParts[pathParts.length - 1];
    
    loadMachineData();
    loadProblems();
    setupEventListeners();
});

function setupEventListeners() {
    // Form submission
    document.getElementById('btnSaveProblem').addEventListener('click', saveProblem);
    
    // Auto-calculate downtime
    document.getElementById('startTime').addEventListener('change', calculateDowntime);
    document.getElementById('endTime').addEventListener('change', calculateDowntime);
    
    // Complete problem button
    document.getElementById('btnCompleteProblem').addEventListener('click', completeProblemNow);
    
    // Photo preview
    document.getElementById('problemPhoto').addEventListener('change', previewPhoto);
    
    // Filters
    document.getElementById('filterStartDate').addEventListener('change', loadProblems);
    document.getElementById('filterEndDate').addEventListener('change', loadProblems);
    document.getElementById('filterStatus').addEventListener('change', loadProblems);
    
    // Refresh button
    document.getElementById('btnRefresh').addEventListener('click', loadProblems);
}

function loadMachineData() {
    fetch(`/impact/api/ctp-machines`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const machine = data.data.find(m => m.nickname === currentMachineId);
                if (machine) {
                    updateStatistics(machine.id);
                }
            }
        });
}

function updateStatistics(machineId) {
    fetch(`/impact/api/ctp-problem-logs?machine_id=${machineId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const logs = data.data;
                
                // Calculate statistics
                const totalProblems = logs.length;
                const activeProblems = logs.filter(log => log.status === 'ongoing').length;
                const totalDowntime = logs.reduce((sum, log) => sum + (log.downtime_hours || 0), 0);
                const avgDowntime = totalProblems > 0 ? totalDowntime / totalProblems : 0;
                
                // Update UI
                document.getElementById('totalProblems').textContent = totalProblems;
                document.getElementById('activeProblems').textContent = activeProblems;
                document.getElementById('totalDowntime').textContent = `${totalDowntime.toFixed(1)} jam`;
                document.getElementById('avgDowntime').textContent = `${avgDowntime.toFixed(1)} jam`;
            }
        });
}

function loadProblems() {
    const startDate = document.getElementById('filterStartDate').value;
    const endDate = document.getElementById('filterEndDate').value;
    const status = document.getElementById('filterStatus').value;
    
    let url = `/impact/api/ctp-problem-logs?machine_nickname=${currentMachineId}`;
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;
    if (status) url += `&status=${status}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tbody = document.querySelector('#problemsTable tbody');
                tbody.innerHTML = '';
                
                data.data.forEach(log => {
                    const row = createProblemDetailRow(log);
                    tbody.innerHTML += row;
                });
            }
        })
        .catch(error => {
            console.error('Error loading problems:', error);
            showToast('Gagal memuat data problem', 'danger');
        });
}

function createProblemDetailRow(log) {
    const statusBadge = log.status === 'completed' 
        ? '<span class="badge bg-success">Selesai</span>'
        : '<span class="badge bg-warning">Berjalan</span>';
    
    const downtime = log.downtime_hours ? `${log.downtime_hours.toFixed(1)} jam` : '-';
    const photo = log.problem_photo 
        ? `<img src="/impact/instance/uploads/${log.problem_photo}" class="photo-preview" onclick="showPhoto('${log.problem_photo}')">`
        : '-';
    
    const actions = log.status === 'ongoing' 
        ? `<button class="btn btn-sm btn-success" onclick="completeProblem(${log.id})">
             <i class="fas fa-check"></i> Selesai
           </button>`
        : `<button class="btn btn-sm btn-info" onclick="editProblem(${log.id})">
             <i class="fas fa-edit"></i> Edit
           </button>
           <button class="btn btn-sm btn-danger" onclick="deleteProblem(${log.id})">
             <i class="fas fa-trash"></i> Hapus
           </button>`;
    
    return `
        <tr>
            <td>${formatDate(log.problem_date)}</td>
            <td>${log.problem_description}</td>
            <td>${log.solution || '-'}</td>
            <td>${log.technician_name || '-'}</td>
            <td>${statusBadge}</td>
            <td>${downtime}</td>
            <td>${photo}</td>
            <td>${actions}</td>
        </tr>
    `;
}

function saveProblem() {
    const form = document.getElementById('addProblemForm');
    const formData = new FormData();
    
    // Get form data
    const problemData = {
        machine_id: getMachineIdByNickname(currentMachineId),
        problem_description: document.getElementById('problemDescription').value,
        technician_type: document.getElementById('technicianType').value,
        technician_name: document.getElementById('technicianName').value,
        solution: document.getElementById('solution').value,
        start_time: document.getElementById('startTime').value,
        end_time: document.getElementById('endTime').value
    };
    
    // Validate required fields
    if (!problemData.problem_description || !problemData.technician_type || !problemData.start_time) {
        showToast('Mohon lengkapi field yang wajib diisi', 'warning');
        return;
    }
    
    // Handle file upload
    const photoFile = document.getElementById('problemPhoto').files[0];
    if (photoFile) {
        formData.append('problem_photo', photoFile);
    }
    
    formData.append('data', JSON.stringify(problemData));
    
    fetch('/impact/api/ctp-problem-logs', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Problem berhasil ditambahkan', 'success');
            bootstrap.Modal.getInstance(document.getElementById('addProblemModal')).hide();
            form.reset();
            loadProblems();
            updateStatistics(getMachineIdByNickname(currentMachineId));
        } else {
            showToast('Gagal menambahkan problem: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('Error saving problem:', error);
        showToast('Gagal menambahkan problem', 'danger');
    });
}

function calculateDowntime() {
    const startTime = document.getElementById('startTime').value;
    const endTime = document.getElementById('endTime').value;
    
    if (startTime && endTime) {
        const start = new Date(startTime);
        const end = new Date(endTime);
        const diff = end - start;
        
        if (diff > 0) {
            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            
            document.getElementById('downtimeCalculation').textContent = 
                `${hours} jam ${minutes} menit`;
        }
    }
}

function completeProblemNow() {
    const now = new Date();
    const endTime = now.toISOString().slice(0, 16);
    document.getElementById('endTime').value = endTime;
    calculateDowntime();
}

function previewPhoto(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('photoPreview').innerHTML = 
                `<img src="${e.target.result}" class="photo-preview" alt="Preview">`;
        };
        reader.readAsDataURL(file);
    }
}

function showPhoto(filename) {
    document.getElementById('modalPhoto').src = `/impact/uploads/${filename}`;
    new bootstrap.Modal(document.getElementById('photoModal')).show();
}

function completeProblem(logId) {
    const endTime = prompt('Masukkan waktu selesai (YYYY-MM-DD HH:MM):');
    if (endTime) {
        fetch(`/impact/api/ctp-problem-logs/${logId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                end_time: endTime
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Problem berhasil diselesaikan', 'success');
                loadProblems();
                updateStatistics(getMachineIdByNickname(currentMachineId));
            } else {
                showToast('Gagal menyelesaikan problem', 'danger');
            }
        });
    }
}

function deleteProblem(logId) {
    if (confirm('Apakah Anda yakin ingin menghapus problem ini?')) {
        fetch(`/impact/api/ctp-problem-logs/${logId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Problem berhasil dihapus', 'success');
                loadProblems();
                updateStatistics(getMachineIdByNickname(currentMachineId));
            } else {
                showToast('Gagal menghapus problem', 'danger');
            }
        });
    }
}

function getMachineIdByNickname(nickname) {
    // This should be implemented based on your machine data
    // For now, return a placeholder
    return 1;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showToast(message, type = 'success') {
    const toastContainer = document.createElement('div');
    toastContainer.style.position = 'fixed';
    toastContainer.style.top = '1rem';
    toastContainer.style.right = '1rem';
    toastContainer.style.zIndex = '1050';
    
    toastContainer.innerHTML = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    document.body.appendChild(toastContainer);
    const toast = new bootstrap.Toast(toastContainer.querySelector('.toast'));
    toast.show();
    
    toastContainer.querySelector('.toast').addEventListener('hidden.bs.toast', () => {
        toastContainer.remove();
    });
}
```

## Initial Data Setup

```python
def initialize_ctp_machines():
    """Initialize CTP machines with default data"""
    machines = [
        {
            'name': 'CTP 1 Suprasetter',
            'nickname': 'ctp-1',
            'status': 'active',
            'description': 'Mesin CTP Suprasetter untuk produksi plate'
        },
        {
            'name': 'CTP 2 Platesetter',
            'nickname': 'ctp-2', 
            'status': 'active',
            'description': 'Mesin CTP Platesetter untuk produksi plate'
        },
        {
            'name': 'CTP 3 Trendsetter',
            'nickname': 'ctp-3',
            'status': 'active',
            'description': 'Mesin CTP Trendsetter untuk produksi plate'
        }
    ]
    
    for machine_data in machines:
        existing = CTPMachine.query.filter_by(nickname=machine_data['nickname']).first()
        if not existing:
            machine = CTPMachine(**machine_data)
            db.session.add(machine)
    
    db.session.commit()
```

## File Upload Configuration

Tambahkan konfigurasi di `config.py`:

```python
# Upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
```

## Database Migration

Buat file migration baru:

```python
# migrations/versions/create_ctp_log_tables.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create ctp_machines table
    op.create_table('ctp_machines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('nickname', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create ctp_problem_logs table
    op.create_table('ctp_problem_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('machine_id', sa.Integer(), nullable=False),
        sa.Column('problem_date', sa.DateTime(), nullable=False),
        sa.Column('problem_description', sa.Text(), nullable=False),
        sa.Column('problem_photo', sa.String(length=255), nullable=True),
        sa.Column('solution', sa.Text(), nullable=True),
        sa.Column('technician_type', sa.String(length=20), nullable=False),
        sa.Column('technician_name', sa.String(length=100), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['machine_id'], ['ctp_machines.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create ctp_notifications table
    op.create_table('ctp_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('machine_id', sa.Integer(), nullable=False),
        sa.Column('log_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['log_id'], ['ctp_problem_logs.id'], ),
        sa.ForeignKeyConstraint(['machine_id'], ['ctp_machines.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('ctp_notifications')
    op.drop_table('ctp_problem_logs')
    op.drop_table('ctp_machines')
```

## Testing Plan

1. **Database Setup Testing**
   - Verify tables are created correctly
   - Test initial machine data insertion
   - Test foreign key constraints

2. **Frontend Testing**
   - Test overview page loads correctly
   - Test machine detail page functionality
   - Test form validation and submission
   - Test photo upload functionality

3. **Backend API Testing**
   - Test all CRUD operations
   - Test authentication and authorization
   - Test file upload handling
   - Test downtime calculation

4. **Integration Testing**
   - Test complete workflow from problem report to resolution
   - Test notification system
   - Test filtering and search functionality
   - Test responsive design on mobile devices

## Deployment Checklist

- [ ] Run database migrations
- [ ] Initialize machine data
- [ ] Create upload directory with proper permissions
- [ ] Test all functionality in development
- [ ] Perform user acceptance testing
- [ ] Deploy to production
- [ ] Monitor for any issues
- [ ] Train users on new functionality

## Future Enhancements

1. **Advanced Reporting**
   - Monthly/quarterly downtime reports
   - Problem categorization and trend analysis
   - Technician performance metrics

2. **Automation Features**
   - Automatic problem detection from machine logs
   - Scheduled maintenance reminders
   - Email/SMS notifications for critical problems

3. **Mobile App**
   - Native mobile application for field technicians
   - Push notifications for urgent problems
   - Offline mode for remote areas

4. **Integration with Other Systems**
   - Integration with maintenance management system
   - Integration with inventory system for spare parts
   - API for third-party monitoring tools
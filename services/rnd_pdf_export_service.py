"""
R&D CloudSphere PDF Export Service

This service handles PDF generation for R&D job details with role-based security.
Regular users can only export tasks for which they are responsible,
while admin users can export all tasks on the job.
"""

import os
import io
from datetime import datetime
from flask import current_app
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from sqlalchemy import and_
from models_rnd import (
    RNDJob, RNDProgressStep, RNDJobProgressAssignment,
    RNDJobTaskAssignment, RNDEvidenceFile, RNDTaskCompletion
)
from models import User
import pytz

# Jakarta timezone
jakarta_tz = pytz.timezone('Asia/Jakarta')


class RNDPDFExportService:
    """Service for exporting R&D job details to PDF with role-based security"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for PDF export"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=20,
            alignment=1,  # Center
            textColor=colors.HexColor('#2c3e50')
        )
        
        # Job ID style (smaller font)
        self.job_id_style = ParagraphStyle(
            'JobID',
            parent=self.styles['Title'],
            fontSize=14,
            spaceAfter=10,
            alignment=1,  # Center
            textColor=colors.HexColor('#2c3e50')
        )
        
        # Section header style
        self.section_header_style = ParagraphStyle(
            'SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#495057'),
            borderWidth=1,
            borderColor=colors.HexColor('#dee2e6'),
            borderPadding=5
        )
        
        # Subsection header style
        self.subsection_header_style = ParagraphStyle(
            'SubsectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor('#6c757d')
        )
        
        # Normal text style
        self.normal_style = ParagraphStyle(
            'Normal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=5,
            alignment=0,  # Left
            textColor=colors.HexColor('#212529')
        )
        
        # Table header style
        self.table_header_style = ParagraphStyle(
            'TableHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=1,  # Center
            textColor=colors.white
        )
        
        # Table cell style
        self.table_cell_style = ParagraphStyle(
            'TableCell',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=0,  # Left
            textColor=colors.HexColor('#212529')
        )
        
        # Small text style
        self.small_style = ParagraphStyle(
            'Small',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=0,  # Left
            textColor=colors.HexColor('#6c757d')
        )
    
    def export_job_to_pdf(self, job_id, user_role, user_id):
        """
        Export R&D job details to PDF with role-based security
        
        Args:
            job_id: ID of the job to export
            user_role: Role of the user making the request ('admin' or other)
            user_id: ID of the user making the request
            
        Returns:
            BytesIO buffer containing the PDF data
        """
        try:
            # Get job with error handling
            job = RNDJob.query.get(job_id)
            if not job:
                raise ValueError(f"Job with ID {job_id} not found")
            
            # Create PDF buffer
            buffer = io.BytesIO()
            
            # Create PDF document with A4 portrait
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                leftMargin=0.75*inch,
                rightMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch,
                title=f"Cloudsphere Job Detail - {job.job_id}",
                author="Impact 360 | Prepress Offset System"
            )
            
            # Build PDF content
            story = []
            
            # Add logo at top (preserve aspect ratio; downscale to fit)
            logo_path = os.path.join(current_app.root_path, 'static', 'img', 'LogoTbk.png')
            if os.path.exists(logo_path):
                logo = Image(logo_path)
                # Set logo dimensions to 6.5 inches wide and 2.5 inches tall
                logo.drawWidth = 4.5*inch
                logo.drawHeight = 1.3*inch
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 0.2*inch))
            
            # Add title
            story.append(Paragraph(f"CLOUDSPHERE JOB DETAIL", self.title_style))
            story.append(Spacer(1, 0.05*inch))  # Reduced spacing
            story.append(Paragraph(f"{job.job_id}", self.job_id_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Add Job Information section
            story.extend(self._create_job_info_section(job))
            
            # Add Tasks section with role-based filtering
            story.extend(self._create_tasks_section(job, user_role, user_id))
            
            # Add Proof Files section with role-based filtering
            story.extend(self._create_evidence_files_section(job, user_role, user_id))
            
            # Add footer
            story.extend(self._create_footer_section())
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            current_app.logger.error(f"Error generating PDF for job {job_id}: {str(e)}")
            raise Exception(f"PDF generation failed: {str(e)}")
    
    def _create_job_info_section(self, job):
        """Create Job Information section for PDF"""
        elements = []
        
        # Section header
        elements.append(Paragraph("Job Information", self.section_header_style))
        
        # Job information table
        job_info_data = [
            ['Field', 'Value'],
            ['Job ID', job.job_id],
            ['Item Name', job.item_name or ''],
            ['Sample Type', job.sample_type or ''],
            ['Priority Level', (job.priority_level or '').title()],
            ['Status', job.status.replace('_', ' ').title() if job.status else ''],
            ['Started At', self._format_datetime(job.started_at)],
            ['Deadline', self._format_datetime(job.deadline_at)],
            ['Finished At', self._format_datetime(job.finished_at)],
            ['Lead Time', self._calculate_lead_time(job)],
            ['Completion', f"{job.completion_percentage or 0:.1f}%"],
            ['Notes', job.notes or '']
        ]
        
        # Create table with proper styling
        job_table = Table(job_info_data, colWidths=[2.5*inch, 4.0*inch])
        job_table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#495057')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            
            # Data row styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),
        ]))
        
        elements.append(job_table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_tasks_section(self, job, user_role, user_id):
        """Create Tasks section with role-based filtering"""
        elements = []
        
        # Section header
        elements.append(Paragraph("Tasks", self.section_header_style))
        
        # Get progress assignments with role-based filtering
        if user_role == 'admin':
            # Admin can see all assignments
            progress_assignments = job.progress_assignments
        else:
            # Regular users can only see their own assignments
            progress_assignments = [
                pa for pa in job.progress_assignments 
                if pa.pic_id == user_id
            ]
        
        if not progress_assignments:
            elements.append(Paragraph("No tasks available for your access level.", self.normal_style))
            elements.append(Spacer(1, 0.3*inch))
            return elements
        
        # Group tasks by progress step
        for assignment in progress_assignments:
            # Add progress step header
            step_name = assignment.progress_step.name if assignment.progress_step else 'Unknown Step'
            elements.append(Paragraph(f"Step: {step_name}", self.subsection_header_style))
            
            # Add PIC information
            pic_name = assignment.pic.name if assignment.pic else 'Unassigned'
            elements.append(Paragraph(f"Person in Charge: {pic_name}", self.small_style))
            elements.append(Paragraph(f"Status: {assignment.status.replace('_', ' ').title()}", self.small_style))
            
            # Get tasks for this assignment
            tasks = assignment.task_assignments if assignment.task_assignments else []
            
            if tasks:
                # Create task table
                task_data = [['Task Name', 'Status', 'Completed At']]
                
                for task in tasks:
                    task_name = task.progress_task.name if task.progress_task else 'Unknown Task'
                    status = task.status.replace('_', ' ').title() if task.status else 'Unknown'
                    completed_at = self._format_datetime(task.completed_at)
                    
                    task_data.append([task_name, status, completed_at])
                
                # Create task table
                task_table = Table(task_data, colWidths=[3*inch, 1.5*inch, 2*inch])
                task_table.setStyle(TableStyle([
                    # Header row styling
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c757d')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                    
                    # Data row styling
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 1), (-1, -1), 'TOP'),
                    
                    # Borders
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
                ]))
                
                elements.append(task_table)
            else:
                elements.append(Paragraph("No tasks found for this step.", self.normal_style))
            
            elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_evidence_files_section(self, job, user_role, user_id):
        """Create Proof Files section with role-based filtering"""
        elements = []
        
        # Section header
        elements.append(Paragraph("Proof Files", self.section_header_style))
        
        # Get evidence files with role-based filtering
        if user_role == 'admin':
            # Admin can see all evidence files
            evidence_files = job.evidence_files.all() if job.evidence_files else []
        else:
            # Regular users can only see evidence files for their assigned steps
            user_assignment_ids = [
                pa.id for pa in job.progress_assignments 
                if pa.pic_id == user_id
            ]
            
            evidence_files = []
            if job.evidence_files:
                evidence_files = job.evidence_files.filter(
                    and_(
                        RNDEvidenceFile.job_progress_assignment_id.in_(user_assignment_ids),
                        RNDEvidenceFile.job_task_assignment_id.in_([
                            ta.id for pa in job.progress_assignments 
                            if pa.pic_id == user_id 
                            for ta in pa.task_assignments or []
                        ])
                    )
                ).all()
        
        if not evidence_files:
            elements.append(Paragraph("No evidence files available for your access level.", self.normal_style))
            elements.append(Spacer(1, 0.3*inch))
            return elements
        
        # Group evidence files by progress step
        evidence_by_step = {}
        for evidence in evidence_files:
            step_name = 'General'
            if evidence.progress_assignment and evidence.progress_assignment.progress_step:
                step_name = evidence.progress_assignment.progress_step.name
            
            if step_name not in evidence_by_step:
                evidence_by_step[step_name] = []
            evidence_by_step[step_name].append(evidence)
        
        # Create evidence sections
        for step_name, files in evidence_by_step.items():
            elements.append(Paragraph(f"Step: {step_name}", self.subsection_header_style))
            
            if files:
                # Create evidence table
                evidence_data = [['File Name', 'Uploaded By', 'Upload Date']]
                
                for file in files:
                    file_name = file.original_filename or file.filename
                    uploader_name = file.uploader.name if file.uploader else 'Unknown'
                    upload_date = self._format_datetime(file.uploaded_at)
                    
                    evidence_data.append([file_name, uploader_name, upload_date])
                
                # Create evidence table
                evidence_table = Table(evidence_data, colWidths=[3.3*inch, 1.5*inch, 1.7*inch])
                evidence_table.setStyle(TableStyle([
                    # Header row styling
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#17a2b8')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                    
                    # Data row styling
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 1), (-1, -1), 'TOP'),
                    
                    # Borders
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
                ]))
                
                elements.append(evidence_table)
            else:
                elements.append(Paragraph("No evidence files found for this step.", self.normal_style))
            
            elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_footer_section(self):
        """Create footer section for PDF"""
        elements = []
        
        # Add page break before footer
        elements.append(PageBreak())
        
        # Footer information
        elements.append(Paragraph(
            f"Generated on {self._format_datetime(datetime.now(jakarta_tz))} by Impact 360 | Prepress Offset System",
            self.small_style
        ))
        
        # Confidentiality notice
        elements.append(Paragraph(
            "This document contains confidential information. Handle with appropriate security.",
            self.small_style
        ))
        
        return elements
    
    def _format_datetime(self, dt):
        """Format datetime for display"""
        if not dt:
            return 'N/A'
        
        if hasattr(dt, 'strftime'):
            return dt.strftime('%d %B %Y %H:%M')
        else:
            # Handle string datetime
            try:
                dt_obj = datetime.fromisoformat(str(dt))
                return dt_obj.strftime('%d %B %Y %H:%M')
            except:
                return str(dt)
    
    def _format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if not size_bytes:
            return 'Unknown'
        
        # Convert to KB
        size_kb = size_bytes / 1024
        if size_kb < 1:
            return f"{size_bytes} bytes"
        elif size_kb < 1024:
            return f"{size_kb:.1f} KB"
        else:
            # Convert to MB
            size_mb = size_kb / 1024
            return f"{size_mb:.1f} MB"
    
    def _calculate_lead_time(self, job):
        """Calculate lead time from job started to finished (or now if still in progress)"""
        try:
            started_at = job.started_at
            finished_at = job.finished_at
            
            if not started_at:
                return 'Not started'
            
            # Use current time if job is not finished
            end_time = finished_at if finished_at else datetime.now(jakarta_tz)
            
            # Convert to datetime objects if they're strings
            if isinstance(started_at, str):
                started_at = datetime.fromisoformat(started_at)
                if started_at.tzinfo is None:
                    started_at = jakarta_tz.localize(started_at)
            
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)
                if end_time.tzinfo is None:
                    end_time = jakarta_tz.localize(end_time)
            
            # Calculate the difference
            diff = end_time - started_at
            
            # Extract days, hours, minutes
            days = diff.days
            hours, remainder = divmod(diff.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            # Format the output
            result = ''
            if days > 0:
                result += f"{days} day{'s' if days > 1 else ''}"
            
            if hours > 0:
                if result:
                    result += ' '
                result += f"{hours} hour{'s' if hours > 1 else ''}"
            
            if minutes > 0:
                if result:
                    result += ' '
                result += f"{minutes} minute{'s' if minutes > 1 else ''}"
            
            # If all components are 0, return "Less than 1 minute"
            if not result:
                result = 'Less than 1 minute'
            
            # Add "(ongoing)" if job is not finished
            if not finished_at:
                result += ' (ongoing)'
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"Error calculating lead time: {str(e)}")
            return 'Error calculating'
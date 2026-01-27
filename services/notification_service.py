"""
Universal Notification Service for Impact 360
Handles creation and distribution of notifications across all modules
"""

import json
import logging
from datetime import datetime
import pytz
from models import db, UniversalNotification, NotificationRecipient, User, Division

logger = logging.getLogger(__name__)
jakarta_tz = pytz.timezone('Asia/Jakarta')


class NotificationService:
    """
    Core service untuk mengelola notifikasi
    - Create notifikasi
    - Send ke users tertentu
    - Mark as read
    - Query notifikasi
    """
    
    @staticmethod
    def create_notification(
        notification_type,
        title,
        message,
        related_resource_type,
        related_resource_id,
        triggered_by_user_id,
        notification_metadata=None
    ):
        """
        Create notifikasi baru
        
        Args:
            notification_type: str (e.g., 'ctp_problem_new', 'rnd_job_created')
            title: str - Judul notifikasi
            message: str - Pesan notifikasi
            related_resource_type: str (e.g., 'ctp_problem', 'rnd_job')
            related_resource_id: int - ID dari resource
            triggered_by_user_id: int - User ID yang trigger notifikasi
            notification_metadata: dict - Additional metadata (opsional)
        
        Returns:
            UniversalNotification object
        """
        try:
            metadata_json = json.dumps(notification_metadata) if notification_metadata else None
            
            notification = UniversalNotification(
                notification_type=notification_type,
                title=title,
                message=message,
                related_resource_type=related_resource_type,
                related_resource_id=related_resource_id,
                triggered_by_user_id=triggered_by_user_id,
                notification_metadata=metadata_json
            )
            
            db.session.add(notification)
            db.session.flush()  # Get notification ID sebelum commit
            
            logger.info(f"Created notification {notification.id}: {notification_type}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            db.session.rollback()
            raise
    
    @staticmethod
    def add_recipients(notification_id, user_ids):
        """
        Add recipients untuk notifikasi
        
        Args:
            notification_id: int - ID notifikasi
            user_ids: list[int] - List of user IDs
        
        Returns:
            list - Created NotificationRecipient objects
        """
        try:
            recipients = []
            for user_id in user_ids:
                # Avoid duplicates
                existing = NotificationRecipient.query.filter_by(
                    notification_id=notification_id,
                    user_id=user_id
                ).first()
                
                if not existing:
                    recipient = NotificationRecipient(
                        notification_id=notification_id,
                        user_id=user_id
                    )
                    db.session.add(recipient)
                    recipients.append(recipient)
            
            db.session.commit()
            logger.info(f"Added {len(recipients)} recipients to notification {notification_id}")
            return recipients
            
        except Exception as e:
            logger.error(f"Error adding recipients: {str(e)}")
            db.session.rollback()
            raise
    
    @staticmethod
    def mark_as_read(notification_id, user_id):
        """
        Mark notifikasi sebagai sudah dibaca untuk user tertentu
        
        Args:
            notification_id: int
            user_id: int
        
        Returns:
            bool - Success status
        """
        try:
            recipient = NotificationRecipient.query.filter_by(
                notification_id=notification_id,
                user_id=user_id
            ).first()
            
            if recipient:
                recipient.is_read = True
                recipient.read_at = datetime.now(jakarta_tz)
                db.session.commit()
                logger.info(f"Marked notification {notification_id} as read for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            db.session.rollback()
            raise
    
    @staticmethod
    def mark_all_as_read(user_id):
        """
        Mark semua notifikasi sebagai dibaca untuk user
        
        Args:
            user_id: int
        
        Returns:
            int - Jumlah notifikasi yang di-mark
        """
        try:
            now = datetime.now(jakarta_tz)
            
            updated = db.session.query(NotificationRecipient).filter(
                NotificationRecipient.user_id == user_id,
                NotificationRecipient.is_read == False
            ).update({
                NotificationRecipient.is_read: True,
                NotificationRecipient.read_at: now
            })
            
            db.session.commit()
            logger.info(f"Marked {updated} notifications as read for user {user_id}")
            return updated
            
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
            db.session.rollback()
            raise
    
    @staticmethod
    def get_user_notifications(user_id, limit=50, offset=0, include_read=True):
        """
        Get notifikasi untuk user
        
        Args:
            user_id: int
            limit: int - Max results
            offset: int - Pagination offset
            include_read: bool - Include read notifications
        
        Returns:
            list - Notifications with user's read status
        """
        try:
            query = (
                db.session.query(UniversalNotification)
                .join(NotificationRecipient)
                .filter(NotificationRecipient.user_id == user_id)
            )
            
            if not include_read:
                query = query.filter(NotificationRecipient.is_read == False)
            
            notifications = query.order_by(
                UniversalNotification.created_at.desc()
            ).limit(limit).offset(offset).all()
            
            # Build response dengan recipient status
            result = []
            for notif in notifications:
                data = notif.to_dict(include_recipient_status=user_id)
                result.append(data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting user notifications: {str(e)}")
            raise
    
    @staticmethod
    def get_unread_count(user_id):
        """
        Get jumlah unread notifications untuk user
        
        Args:
            user_id: int
        
        Returns:
            int - Unread count
        """
        try:
            count = db.session.query(db.func.count(NotificationRecipient.id)).filter(
                NotificationRecipient.user_id == user_id,
                NotificationRecipient.is_read == False
            ).scalar()
            
            return count or 0
            
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            raise


class NotificationDispatcher:
    """
    Business logic untuk dispatch notifikasi ke users berdasarkan rules
    Separates notification creation dari business logic
    """
    
    @staticmethod
    def send_to_division(
        division_id,
        notification_type,
        title,
        message,
        related_resource_type,
        related_resource_id,
        triggered_by_user_id,
        notification_metadata=None,
        include_admins=True
    ):
        """
        Send notifikasi ke semua users di division tertentu
        
        Args:
            division_id: int - Division ID
            include_admins: bool - Include admin users juga
            ... (other params same as create_notification)
        
        Returns:
            dict - {notification_id, recipient_count}
        """
        try:
            # Create notification
            notification = NotificationService.create_notification(
                notification_type=notification_type,
                title=title,
                message=message,
                related_resource_type=related_resource_type,
                related_resource_id=related_resource_id,
                triggered_by_user_id=triggered_by_user_id,
                notification_metadata=notification_metadata
            )
            
            # Get users dari division
            division_users = User.query.filter_by(
                division_id=division_id,
                is_active=True
            ).all()
            
            user_ids = [user.id for user in division_users]
            
            # Add admin users juga
            if include_admins:
                admin_users = User.query.filter_by(
                    role='admin',
                    is_active=True
                ).all()
                admin_ids = [user.id for user in admin_users]
                user_ids = list(set(user_ids + admin_ids))  # Remove duplicates
            
            # Add recipients
            NotificationService.add_recipients(notification.id, user_ids)
            
            logger.info(
                f"Dispatched notification {notification.id} to {len(user_ids)} users "
                f"in division {division_id}"
            )
            
            return {
                'notification_id': notification.id,
                'recipient_count': len(user_ids)
            }
            
        except Exception as e:
            logger.error(f"Error in send_to_division: {str(e)}")
            raise
    
    @staticmethod
    def send_to_admins(
        notification_type,
        title,
        message,
        related_resource_type,
        related_resource_id,
        triggered_by_user_id,
        metadata=None
    ):
        """
        Send notifikasi hanya ke admin users
        
        Returns:
            dict - {notification_id, recipient_count}
        """
        try:
            logger.info(f"send_to_admins: Creating notification type={notification_type}, title={title}")
            
            notification = NotificationService.create_notification(
                notification_type=notification_type,
                title=title,
                message=message,
                related_resource_type=related_resource_type,
                related_resource_id=related_resource_id,
                triggered_by_user_id=triggered_by_user_id,
                notification_metadata=metadata
            )
            
            logger.info(f"send_to_admins: Notification created with id={notification.id}")
            
            admin_users = User.query.filter_by(
                role='admin',
                is_active=True
            ).all()
            
            user_ids = [user.id for user in admin_users]
            logger.info(f"send_to_admins: Found {len(user_ids)} admin users")
            
            NotificationService.add_recipients(notification.id, user_ids)
            
            logger.info(f"Dispatched notification {notification.id} to {len(user_ids)} admins")
            
            return {
                'notification_id': notification.id,
                'recipient_count': len(user_ids)
            }
            
        except Exception as e:
            logger.error(f"Error in send_to_admins: {str(e)}")
            raise
    
    @staticmethod
    def send_to_specific_users(
        user_ids,
        notification_type,
        title,
        message,
        related_resource_type,
        related_resource_id,
        triggered_by_user_id,
        metadata=None
    ):
        """
        Send notifikasi ke specific users
        
        Args:
            user_ids: list[int] - List of user IDs
            ... (other params)
        
        Returns:
            dict - {notification_id, recipient_count}
        """
        try:
            notification = NotificationService.create_notification(
                notification_type=notification_type,
                title=title,
                message=message,
                related_resource_type=related_resource_type,
                related_resource_id=related_resource_id,
                triggered_by_user_id=triggered_by_user_id,
                notification_metadata=metadata
            )
            
            NotificationService.add_recipients(notification.id, user_ids)
            
            logger.info(
                f"Dispatched notification {notification.id} to {len(user_ids)} specific users"
            )
            
            return {
                'notification_id': notification.id,
                'recipient_count': len(user_ids)
            }
            
        except Exception as e:
            logger.error(f"Error in send_to_specific_users: {str(e)}")
            raise
    
    # --- CTP Production Dispatchers ---
    
    @staticmethod
    def dispatch_ctp_problem_new(machine_name, machine_id, machine_nickname, problem_id, problem_description, triggered_by_user_id):
        """
        Dispatch notifikasi ketika problem baru ditambahkan di CTP
        Ke: Semua users di CTP division + Admins
        
        Args:
            machine_name: str
            machine_id: int
            machine_nickname: str - e.g. 'ctp1', 'ctp2'
            problem_id: int - CTP Problem Log ID
            problem_description: str
            triggered_by_user_id: int
        """
        try:
            # CTP Division ID = 1
            CTP_DIVISION_ID = 1
            
            title = f"🚨 Problem Baru pada {machine_name}"
            message = f"Problem baru terdeteksi: {problem_description[:100]}..."
            
            notification_metadata = {
                'machine_id': machine_id,
                'machine_name': machine_name,
                'machine_nickname': machine_nickname,
                'problem_id': problem_id,
                'icon': 'warning'
            }
            
            return NotificationDispatcher.send_to_division(
                division_id=CTP_DIVISION_ID,
                notification_type='ctp_problem_new',
                title=title,
                message=message,
                related_resource_type='ctp_problem',
                related_resource_id=problem_id,
                triggered_by_user_id=triggered_by_user_id,
                notification_metadata=notification_metadata,
                include_admins=True
            )
            
        except Exception as e:
            logger.error(f"Error in dispatch_ctp_problem_new: {str(e)}")
            raise
    
    @staticmethod
    def dispatch_ctp_problem_resolved(machine_name, machine_id, machine_nickname, problem_id, triggered_by_user_id):
        """
        Dispatch notifikasi ketika problem sudah diselesaikan
        Ke: Semua users di CTP division + Admins
        
        Args:
            machine_name: str
            machine_id: int
            machine_nickname: str - e.g. 'ctp1', 'ctp2'
            problem_id: int
            triggered_by_user_id: int
        """
        try:
            CTP_DIVISION_ID = 1
            
            title = f"✅ Problem pada {machine_name} Selesai"
            message = f"Problem pada {machine_name} sudah berhasil diselesaikan"
            
            notification_metadata = {
                'machine_id': machine_id,
                'machine_name': machine_name,
                'machine_nickname': machine_nickname,
                'problem_id': problem_id,
                'icon': 'check'
            }
            
            return NotificationDispatcher.send_to_division(
                division_id=CTP_DIVISION_ID,
                notification_type='ctp_problem_resolved',
                title=title,
                message=message,
                related_resource_type='ctp_problem',
                related_resource_id=problem_id,
                triggered_by_user_id=triggered_by_user_id,
                notification_metadata=notification_metadata,
                include_admins=True
            )
            
        except Exception as e:
            logger.error(f"Error in dispatch_ctp_problem_resolved: {str(e)}")
            raise
    
    # --- RND Production Dispatchers ---
    
    @staticmethod
    def dispatch_rnd_job_created(job_db_id, job_id, item_name, sample_type, priority_level, triggered_by_user_id):
        """
        Dispatch notifikasi ketika R&D job baru dibuat
        Ke: Semua users di RND division + Admins
        
        Args:
            job_db_id: int - Database ID of RNDJob
            job_id: str - e.g. 'RND-20260112-001'
            item_name: str - Name of item
            sample_type: str - Type of sample (Design, Mastercard, Blank, etc.)
            priority_level: str - Low, Middle, High
            triggered_by_user_id: int
        """
        try:
            # RND Division ID = 6
            RND_DIVISION_ID = 6
            
            title = f"📋 R&D Job Baru: {item_name}"
            message = f"Job {job_id} untuk {sample_type} ({priority_level} Priority) telah dibuat"
            
            notification_metadata = {
                'job_db_id': job_db_id,
                'job_id': job_id,
                'item_name': item_name,
                'sample_type': sample_type,
                'priority_level': priority_level,
                'icon': 'clipboard'
            }
            
            return NotificationDispatcher.send_to_division(
                division_id=RND_DIVISION_ID,
                notification_type='rnd_job_created',
                title=title,
                message=message,
                related_resource_type='rnd_job',
                related_resource_id=job_db_id,
                triggered_by_user_id=triggered_by_user_id,
                notification_metadata=notification_metadata,
                include_admins=True
            )
            
        except Exception as e:
            logger.error(f"Error in dispatch_rnd_job_created: {str(e)}")
            raise
    
    @staticmethod
    def dispatch_rnd_job_completed(job_db_id, job_id, item_name, sample_type, triggered_by_user_id):
        """
        Dispatch notifikasi ketika R&D job selesai
        Ke: Semua users di RND division + Admins
        
        Args:
            job_db_id: int - Database ID of RNDJob
            job_id: str - e.g. 'RND-20260112-001'
            item_name: str - Name of item
            sample_type: str - Type of sample
            triggered_by_user_id: int
        """
        try:
            # RND Division ID = 6
            RND_DIVISION_ID = 6
            
            title = f"✅ R&D Job Selesai: {item_name}"
            message = f"Job {job_id} untuk {sample_type} telah selesai"
            
            notification_metadata = {
                'job_db_id': job_db_id,
                'job_id': job_id,
                'item_name': item_name,
                'sample_type': sample_type,
                'icon': 'check'
            }
            
            return NotificationDispatcher.send_to_division(
                division_id=RND_DIVISION_ID,
                notification_type='rnd_job_completed',
                title=title,
                message=message,
                related_resource_type='rnd_job',
                related_resource_id=job_db_id,
                triggered_by_user_id=triggered_by_user_id,
                notification_metadata=notification_metadata,
                include_admins=True
            )
            
        except Exception as e:
            logger.error(f"Error in dispatch_rnd_job_completed: {str(e)}")
            raise
    
    @staticmethod
    def dispatch_rnd_step_completed(job_db_id, job_id, item_name, step_name, pic_name, triggered_by_user_id):
        """
        Dispatch notifikasi ketika progress step di R&D job selesai
        Ke: Semua users di RND division + Admins
        
        Args:
            job_db_id: int - Database ID of RNDJob
            job_id: str - e.g. 'RND-20260112-001'
            item_name: str - Name of item
            step_name: str - Name of completed step
            pic_name: str - Name of PIC who completed
            triggered_by_user_id: int
        """
        try:
            # RND Division ID = 6
            RND_DIVISION_ID = 6
            
            title = f"🚀 Step Selesai: {step_name}"
            message = f"Job {job_id} - Step '{step_name}' telah selesai oleh {pic_name}"
            
            notification_metadata = {
                'job_db_id': job_db_id,
                'job_id': job_id,
                'item_name': item_name,
                'step_name': step_name,
                'pic_name': pic_name,
                'icon': 'rocket'
            }
            
            return NotificationDispatcher.send_to_division(
                division_id=RND_DIVISION_ID,
                notification_type='rnd_step_completed',
                title=title,
                message=message,
                related_resource_type='rnd_job',
                related_resource_id=job_db_id,
                triggered_by_user_id=triggered_by_user_id,
                notification_metadata=notification_metadata,
                include_admins=True
            )
            
        except Exception as e:
            logger.error(f"Error in dispatch_rnd_step_completed: {str(e)}")
            raise
    @staticmethod
    def dispatch_5w1h_entry_status_changed(entry_id, entry_title, old_status, new_status, updated_by_user_id, updated_by_name):
        """
        Dispatch notifikasi ketika status 5W1H entry berubah
        Ke: Semua Admin users
        
        Args:
            entry_id: int - Database ID of FiveWOneH entry
            entry_title: str - Title of the 5W1H entry
            old_status: str - Previous status (e.g., 'draft')
            new_status: str - New status (e.g., 'open', 'closed')
            updated_by_user_id: int - User ID who updated the entry
            updated_by_name: str - Name of the user who updated the entry
        """
        try:
            # Create appropriate icon and title based on new status
            status_icons = {
                'open': '🔓',
                'closed': '✅'
            }
            status_icon = status_icons.get(new_status, '📋')
            status_label = new_status.capitalize()
            
            title = f"{status_icon} Status Form 5W1H berubah: {entry_title}"
            message = f"Status berubah dari {old_status.capitalize()} menjadi {status_label} oleh {updated_by_name}"
            
            notification_metadata = {
                'entry_id': entry_id,
                'entry_title': entry_title,
                'old_status': old_status,
                'new_status': new_status,
                'updated_by_user_id': updated_by_user_id,
                'updated_by_name': updated_by_name,
                'icon': 'check-circle'
            }
            
            return NotificationDispatcher.send_to_admins(
                notification_type='5w1h_entry_status_changed',
                title=title,
                message=message,
                related_resource_type='5w1h_entry',
                related_resource_id=entry_id,
                triggered_by_user_id=updated_by_user_id,
                metadata=notification_metadata
            )
            
        except Exception as e:
            logger.error(f"Error in dispatch_5w1h_entry_status_changed: {str(e)}")
            raise
    @staticmethod
    def dispatch_team_note_new(job_db_id, job_id, item_name, note_author_id, note_author_name, note_content, triggered_by_user_id):
        """
        Dispatch notifikasi ketika note baru ditambahkan ke job team notes
        Ke: Semua PICs assigned ke job + Admins, KECUALI the note author
        
        Args:
            job_db_id: int - Database ID of RNDJob
            job_id: str - e.g. 'RND-20260112-001'
            item_name: str - Name of item
            note_author_id: int - User ID who wrote the note
            note_author_name: str - Name of note author
            note_content: str - Content of the note (for preview)
            triggered_by_user_id: int
        """
        try:
            from models_rnd import RNDJobProgressAssignment
            
            # Get all PICs assigned to this job
            pic_assignments = RNDJobProgressAssignment.query.filter_by(job_id=job_db_id).all()
            pic_ids = [assignment.pic_id for assignment in pic_assignments]
            
            # Get all admin users
            admin_users = User.query.filter_by(
                role='admin',
                is_active=True
            ).all()
            admin_ids = [user.id for user in admin_users]
            
            # Combine PICs + Admins, remove duplicates, EXCLUDE note author
            recipient_ids = list(set(pic_ids + admin_ids))
            recipient_ids = [uid for uid in recipient_ids if uid != note_author_id]
            
            # Skip notification if no recipients (e.g., author is only person)
            if not recipient_ids:
                logger.info(f"No recipients for team note notification (author is only person)")
                return {'notification_id': None, 'recipient_count': 0}
            
            # Truncate note content for preview (max 100 chars)
            note_preview = note_content[:100] + ('...' if len(note_content) > 100 else '')
            
            title = f"💬 Team Note dari {note_author_name}"
            message = f"Job {job_id}: {note_preview}"
            
            notification_metadata = {
                'job_db_id': job_db_id,
                'job_id': job_id,
                'item_name': item_name,
                'note_author_id': note_author_id,
                'note_author_name': note_author_name,
                'note_preview': note_preview,
                'icon': 'message'
            }
            
            # Create notification
            notification = NotificationService.create_notification(
                notification_type='rnd_team_note_new',
                title=title,
                message=message,
                related_resource_type='rnd_job',
                related_resource_id=job_db_id,
                triggered_by_user_id=triggered_by_user_id,
                notification_metadata=notification_metadata
            )
            
            # Add recipients (PICs + admins, excluding author)
            NotificationService.add_recipients(notification.id, recipient_ids)
            
            logger.info(
                f"Dispatched team note notification {notification.id} for job {job_id} "
                f"to {len(recipient_ids)} recipients (excluding author {note_author_id})"
            )
            
            return {
                'notification_id': notification.id,
                'recipient_count': len(recipient_ids)
            }
            
        except Exception as e:
            logger.error(f"Error in dispatch_team_note_new: {str(e)}")
            raise
    # --- Tools 5W1H Dispatchers ---
    
    @staticmethod
    def dispatch_5w1h_entry_created(entry_id, entry_title, created_by_user_id, created_by_name):
        """
        Dispatch notifikasi ketika 5W1H entry baru dibuat
        Ke: Semua Admin users
        
        Args:
            entry_id: int - Database ID of FiveWOneH entry
            entry_title: str - Title of the 5W1H entry
            created_by_user_id: int - User ID who created the entry
            created_by_name: str - Name of the user who created the entry
        """
        try:
            title = f"📝 Form 5W1H Baru: {entry_title}"
            message = f"Form 5W1H baru telah dibuat oleh {created_by_name}"
            
            notification_metadata = {
                'entry_id': entry_id,
                'entry_title': entry_title,
                'created_by_user_id': created_by_user_id,
                'created_by_name': created_by_name,
                'icon': 'clipboard-list'
            }
            
            return NotificationDispatcher.send_to_admins(
                notification_type='5w1h_entry_created',
                title=title,
                message=message,
                related_resource_type='5w1h_entry',
                related_resource_id=entry_id,
                triggered_by_user_id=created_by_user_id,
                metadata=notification_metadata
            )
            
        except Exception as e:
            logger.error(f"Error in dispatch_5w1h_entry_created: {str(e)}")
            raise
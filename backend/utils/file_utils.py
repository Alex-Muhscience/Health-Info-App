import uuid
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional
import magic
from flask import current_app
from werkzeug.utils import secure_filename

# Supported file types with their MIME types and extensions
ALLOWED_EXTENSIONS = {
    'images': {
        'mimes': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
        'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    },
    'documents': {
        'mimes': ['application/pdf', 'application/msword',
                  'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        'extensions': ['.pdf', '.doc', '.docx']
    },
    'spreadsheets': {
        'mimes': ['application/vnd.ms-excel',
                  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        'extensions': ['.xls', '.xlsx']
    }
}


class FileUtils:
    @staticmethod
    def allowed_file(filename: str, file_type: str = 'images') -> bool:
        """
        Check if the file extension is allowed
        Args:
            filename: Name of the file
            file_type: Type of file (images/documents/spreadsheets)
        Returns:
            bool: True if allowed, False otherwise
        """
        if '.' not in filename:
            return False

        ext = FileUtils.get_file_extension(filename)
        allowed_exts = ALLOWED_EXTENSIONS.get(file_type, {}).get('extensions', [])
        return ext in allowed_exts

    @staticmethod
    def validate_file_mime(file_stream, file_type: str = 'images') -> bool:
        """
        Validate file MIME type using python-magic
        Args:
            file_stream: File stream or path
            file_type: Type of file to validate against
        Returns:
            bool: True if valid, False otherwise
        """
        mime = magic.Magic(mime=True)
        file_mime = mime.from_buffer(file_stream.read(1024))
        file_stream.seek(0)  # Reset file pointer

        allowed_mimes = ALLOWED_EXTENSIONS.get(file_type, {}).get('mimes', [])
        return file_mime in allowed_mimes

    @staticmethod
    def generate_unique_filename(filename: str) -> str:
        """
        Generate a unique filename with UUID and timestamp
        Args:
            filename: Original filename
        Returns:
            str: Unique filename
        """
        ext = FileUtils.get_file_extension(filename)
        secure_name = secure_filename(Path(filename).stem)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{secure_name}_{timestamp}_{unique_id}{ext}"

    @staticmethod
    def get_upload_folder(subfolder: Optional[str] = None) -> Path:
        """
        Get the upload folder path, creating it if it doesn't exist
        Args:
            subfolder: Optional subfolder within upload directory
        Returns:
            Path: Path to upload directory
        """
        upload_folder = Path(current_app.config['UPLOAD_FOLDER'])
        if subfolder:
            upload_folder = upload_folder / subfolder

        upload_folder.mkdir(parents=True, exist_ok=True)
        return upload_folder

    @staticmethod
    def save_file(file_stream, filename: str, subfolder: Optional[str] = None) -> Tuple[bool, str]:
        """
        Save uploaded file to the filesystem
        Args:
            file_stream: File stream to save
            filename: Name to save the file as
            subfolder: Optional subfolder to save in
        Returns:
            Tuple: (success: bool, message: str)
        """
        try:
            upload_path = FileUtils.get_upload_folder(subfolder)
            file_path = upload_path / filename

            file_stream.save(file_path)
            return True, str(file_path.relative_to(current_app.config['UPLOAD_FOLDER']))
        except Exception as e:
            current_app.logger.error(f"Error saving file: {str(e)}")
            return False, str(e)

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        Delete a file from the filesystem
        Args:
            file_path: Relative path to file from upload folder
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            full_path = Path(current_app.config['UPLOAD_FOLDER']) / file_path
            if full_path.exists():
                full_path.unlink()
                return True
            return False
        except Exception as e:
            current_app.logger.error(f"Error deleting file: {str(e)}")
            return False

    @staticmethod
    def get_file_url(file_path: str) -> str:
        """
        Generate URL for accessing the file
        Args:
            file_path: Relative path to file from upload folder
        Returns:
            str: Full URL to access the file
        """
        if not file_path:
            return ""

        return f"{current_app.config['FILE_SERVER_BASE_URL']}/{file_path}"

    @staticmethod
    def cleanup_old_files(days: int = 30, subfolder: Optional[str] = None) -> Tuple[int, int]:
        """
        Clean up files older than specified days
        Args:
            days: Number of days to keep files
            subfolder: Optional subfolder to clean
        Returns:
            Tuple: (files_deleted: int, total_files: int)
        """
        folder = FileUtils.get_upload_folder(subfolder)
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)

        files_deleted = 0
        total_files = 0

        for item in folder.iterdir():
            if item.is_file():
                total_files += 1
                if item.stat().st_mtime < cutoff_time:
                    try:
                        item.unlink()
                        files_deleted += 1
                    except Exception as e:
                        current_app.logger.error(f"Error deleting old file {item}: {str(e)}")

        return files_deleted, total_files

    @staticmethod
    def get_file_extension(filename: str, include_dot: bool = True) -> str:
        """
        Get the file extension from a filename
        Args:
            filename: The filename or path to extract extension from
            include_dot: Whether to include the dot in the extension
        Returns:
            str: The file extension (e.g. '.jpg' or 'jpg')
        """
        if not filename:
            return ''

        path = Path(filename)
        ext = path.suffix.lower()

        if not include_dot and ext.startswith('.'):
            ext = ext[1:]

        return ext
import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from backend.models import FileUpload, Client
from backend import db
from backend.schemas import file_upload_schema, file_uploads_schema
from backend.utils.auth import token_required
from backend.utils.file_utils import FileUtils

uploads_bp = Blueprint('uploads', __name__, url_prefix='/api/uploads')


@uploads_bp.route('/', methods=['GET'])
@token_required
def list_uploads(current_user):
    """
    List all file uploads
    ---
    tags:
      - Uploads
    security:
      - BearerAuth: []
    parameters:
      - name: client_id
        in: query
        type: integer
        required: false
    responses:
      200:
        description: List of uploads
        schema:
          type: array
          items:
            $ref: '#/definitions/FileUpload'
    """
    query = FileUpload.query

    if 'client_id' in request.args:
        client = Client.query.get_or_404(request.args['client_id'])
        query = query.filter_by(client_id=client.id)

    # For non-admins, only show their own uploads
    if current_user.role not in ['admin', 'practitioner']:
        query = query.filter_by(uploaded_by=current_user.id)

    uploads = query.order_by(FileUpload.uploaded_at.desc()).all()
    return jsonify(file_uploads_schema.dump(uploads))


@uploads_bp.route('/', methods=['POST'])
@token_required
def upload_file(current_user):
    """
    Upload a new file
    ---
    tags:
      - Uploads
    security:
      - BearerAuth: []
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
      - name: client_id
        in: formData
        type: integer
        required: false
      - name: description
        in: formData
        type: string
        required: false
    responses:
      201:
        description: File uploaded
        schema:
          $ref: '#/definitions/FileUpload'
      400:
        description: Invalid file
      404:
        description: Client not found
    """
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if not FileUtils.allowed_file(file.filename):
        return jsonify({'message': 'File type not allowed'}), 400

    # Verify client exists if specified
    client_id = request.form.get('client_id')
    if client_id:
        Client.query.get_or_404(client_id)

    # Create secure filename with UUID
    original_filename = secure_filename(file.filename)
    file_ext = FileUtils.get_file_extension(original_filename)
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"

    # Ensure upload directory exists
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(upload_dir, unique_filename)
    file.save(file_path)

    # Create database record
    new_upload = FileUpload(
        original_filename=original_filename,
        stored_filename=unique_filename,
        file_path=file_path,
        file_type=file_ext[1:].lower(),
        file_size=os.path.getsize(file_path),
        description=request.form.get('description', ''),
        client_id=client_id,
        uploaded_by=current_user.id
    )

    db.session.add(new_upload)
    db.session.commit()

    return jsonify(file_upload_schema.dump(new_upload)), 201


@uploads_bp.route('/<int:upload_id>', methods=['GET'])
@token_required
def download_file(current_user, upload_id):
    """
    Download a file
    ---
    tags:
      - Uploads
    security:
      - BearerAuth: []
    parameters:
      - name: upload_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: File content
        schema:
          type: file
      403:
        description: Forbidden
      404:
        description: File not found
    """
    upload = FileUpload.query.get_or_404(upload_id)

    # Authorization check
    if current_user.role not in ['admin', 'practitioner'] and \
            upload.uploaded_by != current_user.id:
        return jsonify({'message': 'Access denied'}), 403

    if not os.path.exists(upload.file_path):
        return jsonify({'message': 'File not found on server'}), 404

    return current_app.send_file(upload.file_path, as_attachment=True)


@uploads_bp.route('/<int:upload_id>', methods=['DELETE'])
@token_required
def delete_file(current_user, upload_id):
    """
    Delete a file
    ---
    tags:
      - Uploads
    security:
      - BearerAuth: []
    parameters:
      - name: upload_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: File deleted
      403:
        description: Forbidden
      404:
        description: File not found
    """
    upload = FileUpload.query.get_or_404(upload_id)

    # Authorization check
    if current_user.role not in ['admin', 'practitioner'] and \
            upload.uploaded_by != current_user.id:
        return jsonify({'message': 'Access denied'}), 403

    # Delete physical file
    if os.path.exists(upload.file_path):
        os.remove(upload.file_path)

    # Delete database record
    db.session.delete(upload)
    db.session.commit()

    return jsonify({'message': 'File deleted successfully'})


from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from datetime import datetime
import os
import uuid
import json

report_block_bp = Blueprint('report_block', __name__, url_prefix='/user')

ALLOWED_EVIDENCE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.pdf'}
MAX_EVIDENCE_FILES = 5
MAX_EVIDENCE_SIZE  = 10 * 1024 * 1024  # 10 MB per file


def _save_evidence_files(files):
    """Save uploaded evidence files and return list of saved filenames."""
    saved = []
    folder = os.path.join(current_app.root_path, 'static', 'uploads', 'report_evidence')
    os.makedirs(folder, exist_ok=True)

    for f in files:
        if not f or not f.filename:
            continue

        ext = os.path.splitext(f.filename.lower())[1]
        if ext not in ALLOWED_EVIDENCE_EXTENSIONS:
            continue

        f.seek(0, 2)
        size = f.tell()
        f.seek(0)
        if size > MAX_EVIDENCE_SIZE:
            continue

        filename = f"evidence_{current_user.id}_{uuid.uuid4().hex[:10]}{ext}"
        f.save(os.path.join(folder, filename))
        saved.append(filename)

        if len(saved) >= MAX_EVIDENCE_FILES:
            break

    return saved


@report_block_bp.route('/block/<int:target_id>', methods=['POST'])
@login_required
def block_user(target_id):
    from models import db, User, UserBlock, Follow

    if target_id == current_user.id:
        return jsonify({'error': 'Cannot block yourself'}), 400

    target = db.session.get(User, target_id)
    if not target:
        return jsonify({'error': 'User not found'}), 404

    existing = UserBlock.query.filter_by(
        blocker_id=current_user.id, blocked_id=target_id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'action': 'unblocked', 'message': f'You unblocked {target.username}.'})

    block = UserBlock(blocker_id=current_user.id, blocked_id=target_id)
    db.session.add(block)

    # Remove follow relationships in both directions
    Follow.query.filter_by(follower_id=current_user.id, followed_id=target_id).delete()
    Follow.query.filter_by(follower_id=target_id, followed_id=current_user.id).delete()

    db.session.commit()
    return jsonify({'action': 'blocked', 'message': f'You blocked {target.username}.'})


@report_block_bp.route('/report/<int:target_id>', methods=['POST'])
@login_required
def report_user(target_id):
    from models import db, User, UserReport, AdminNotification

    if target_id == current_user.id:
        return jsonify({'error': 'Cannot report yourself'}), 400

    target = db.session.get(User, target_id)
    if not target:
        return jsonify({'error': 'User not found'}), 404

    # Support both JSON and multipart/form-data
    if request.content_type and 'multipart/form-data' in request.content_type:
        reason = (request.form.get('reason') or '').strip()
        desc   = (request.form.get('description') or '').strip()
        files  = request.files.getlist('evidence')
    else:
        data   = request.get_json() or {}
        reason = (data.get('reason') or '').strip()
        desc   = (data.get('description') or '').strip()
        files  = []

    if not reason:
        return jsonify({'error': 'Reason is required'}), 400

    existing = UserReport.query.filter_by(
        reporter_id=current_user.id, reported_id=target_id
    ).first()
    if existing:
        return jsonify({'error': 'You have already reported this user.'}), 409

    # Save evidence files
    saved_files = _save_evidence_files(files) if files else []

    report = UserReport(
        reporter_id    = current_user.id,
        reported_id    = target_id,
        reason         = reason,
        description    = desc,
        evidence_files = json.dumps(saved_files) if saved_files else None,
    )
    db.session.add(report)

    evidence_note = f' ({len(saved_files)} file(s) attached)' if saved_files else ''
    notif = AdminNotification(
        type    = 'user_report',
        message = f'<strong>{current_user.username}</strong> reported <strong>{target.username}</strong> for: {reason}{evidence_note}',
        user_id = target_id,
    )
    db.session.add(notif)
    db.session.commit()

    return jsonify({'action': 'reported', 'message': 'Report submitted. Our team will review it shortly.'})


@report_block_bp.route('/block-status/<int:target_id>', methods=['GET'])
@login_required
def block_status(target_id):
    from models import UserBlock
    is_blocked = bool(UserBlock.query.filter_by(
        blocker_id=current_user.id, blocked_id=target_id
    ).first())
    return jsonify({'is_blocked': is_blocked})
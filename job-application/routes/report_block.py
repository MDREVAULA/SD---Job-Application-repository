from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime

report_block_bp = Blueprint('report_block', __name__, url_prefix='/user')


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

    # ── Block ──────────────────────────────────────────────────
    block = UserBlock(blocker_id=current_user.id, blocked_id=target_id)
    db.session.add(block)

    # ── Remove follow relationships in both directions ──────────
    # blocker → blocked
    Follow.query.filter_by(
        follower_id=current_user.id, followed_id=target_id
    ).delete()
    # blocked → blocker
    Follow.query.filter_by(
        follower_id=target_id, followed_id=current_user.id
    ).delete()

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

    data   = request.get_json() or {}
    reason = (data.get('reason') or '').strip()
    desc   = (data.get('description') or '').strip()

    if not reason:
        return jsonify({'error': 'Reason is required'}), 400

    existing = UserReport.query.filter_by(
        reporter_id=current_user.id, reported_id=target_id
    ).first()
    if existing:
        return jsonify({'error': 'You have already reported this user.'}), 409

    report = UserReport(
        reporter_id=current_user.id,
        reported_id=target_id,
        reason=reason,
        description=desc,
    )
    db.session.add(report)

    notif = AdminNotification(
        type='user_report',
        message=f'<strong>{current_user.username}</strong> reported <strong>{target.username}</strong> for: {reason}',
        user_id=target_id,
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
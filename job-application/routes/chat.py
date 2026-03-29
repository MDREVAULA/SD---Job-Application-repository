from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User, Follow, Message, ApplicantProfile, RecruiterProfile, HRProfile
from datetime import datetime
from sqlalchemy import or_, and_

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


# =========================
# HELPERS
# =========================
def get_display_name(user):
    """Return full name from whichever profile type the user has."""
    if user.role == "applicant":
        p = ApplicantProfile.query.filter_by(user_id=user.id).first()
        if p and p.first_name:
            return f"{p.first_name} {p.last_name}".strip()
    elif user.role == "recruiter":
        p = RecruiterProfile.query.filter_by(user_id=user.id).first()
        if p and p.first_name:
            return f"{p.first_name} {p.surname}".strip()
    elif user.role == "hr":
        p = HRProfile.query.filter_by(user_id=user.id).first()
        if p and p.first_name:
            return f"{p.first_name} {p.last_name}".strip()
    return user.username


def get_company_name(user):
    """Return company name for recruiters / HR."""
    if user.role == "recruiter":
        p = RecruiterProfile.query.filter_by(user_id=user.id).first()
        return p.company_name if p else None
    if user.role == "hr":
        # HR was created_by a recruiter — get that recruiter's company
        if user.created_by:
            recruiter = User.query.get(user.created_by)
            if recruiter:
                p = RecruiterProfile.query.filter_by(user_id=recruiter.id).first()
                return p.company_name if p else None
    return None


def build_user_card(user, current_user_id=None):
    """Return a dict with everything needed to render a user card."""
    company = get_company_name(user)
    is_following = False
    if current_user_id:
        is_following = Follow.query.filter_by(
            follower_id=current_user_id, followed_id=user.id
        ).first() is not None

    return {
        "id": user.id,
        "username": user.username,
        "display_name": get_display_name(user),
        "role": user.role,
        "company": company,
        "profile_picture": user.profile_picture,
        "is_following": is_following,
        "follower_count": Follow.query.filter_by(followed_id=user.id).count(),
    }


# =========================
# PEOPLE PAGE
# (search + follow — guests can view but not follow)
# =========================
@chat_bp.route("/people")
def people():
    query = request.args.get("q", "").strip()
    role_filter = request.args.get("role", "").strip()

    # Exclude admin accounts from people search
    users_query = User.query.filter(User.role != "admin")

    if current_user.is_authenticated:
        # Don't show the current user to themselves
        users_query = users_query.filter(User.id != current_user.id)

    if query:
        users_query = users_query.filter(
            or_(
                User.username.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%")
            )
        )

    if role_filter in ["applicant", "recruiter", "hr"]:
        users_query = users_query.filter(User.role == role_filter)

    # Only show verified / approved users
    users_query = users_query.filter(
        or_(
            User.verification_status == "Approved",
            User.role == "applicant",  # applicants may be pending but still searchable
            User.role == "hr"          # HR accounts are created by recruiters, not admin-verified
        )
    )

    users = users_query.order_by(User.username).all()

    current_id = current_user.id if current_user.is_authenticated else None
    user_cards = [build_user_card(u, current_id) for u in users]

    return render_template(
        "chat/people.html",
        user_cards=user_cards,
        query=query,
        role_filter=role_filter
    )


# =========================
# FOLLOW / UNFOLLOW  (AJAX)
# =========================
@chat_bp.route("/follow/<int:target_id>", methods=["POST"])
@login_required
def follow(target_id):
    target = User.query.get_or_404(target_id)

    if target.id == current_user.id:
        return jsonify({"error": "Cannot follow yourself"}), 400

    existing = Follow.query.filter_by(
        follower_id=current_user.id, followed_id=target.id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        action = "unfollowed"
    else:
        follow = Follow(follower_id=current_user.id, followed_id=target.id)
        db.session.add(follow)
        db.session.commit()
        action = "followed"

    follower_count = Follow.query.filter_by(followed_id=target.id).count()
    return jsonify({"action": action, "follower_count": follower_count})


# =========================
# INBOX
# Lists all conversations (unique people the current user has messaged/received from)
# =========================
@chat_bp.route("/inbox")
@login_required
def inbox():
    # Get all users the current user has a conversation with
    sent_to = db.session.query(Message.receiver_id).filter_by(sender_id=current_user.id)
    received_from = db.session.query(Message.sender_id).filter_by(receiver_id=current_user.id)

    contact_ids = set(
        [r[0] for r in sent_to.all()] +
        [r[0] for r in received_from.all()]
    )

    conversations = []
    for uid in contact_ids:
        user = User.query.get(uid)
        if not user:
            continue

        last_msg = Message.query.filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == uid),
                and_(Message.sender_id == uid, Message.receiver_id == current_user.id)
            )
        ).order_by(Message.created_at.desc()).first()

        unread_count = Message.query.filter_by(
            sender_id=uid, receiver_id=current_user.id, is_read=False
        ).count()

        conversations.append({
            "user": user,
            "display_name": get_display_name(user),
            "company": get_company_name(user),
            "last_message": last_msg,
            "unread_count": unread_count,
        })

    # Sort by most recent message
    conversations.sort(
        key=lambda c: c["last_message"].created_at if c["last_message"] else datetime.min,
        reverse=True
    )

    # Count total unread for nav badge
    total_unread = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()

    return render_template(
        "chat/inbox.html",
        conversations=conversations,
        active_user=None,
        messages=[],
        total_unread=total_unread
    )


# =========================
# CONVERSATION with a specific user
# =========================
@chat_bp.route("/inbox/<int:other_id>")
@login_required
def conversation(other_id):
    other = User.query.get_or_404(other_id)

    # Mark all messages from other → current_user as read
    Message.query.filter_by(
        sender_id=other_id,
        receiver_id=current_user.id,
        is_read=False
    ).update({"is_read": True})
    db.session.commit()

    # Fetch full conversation
    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == other_id),
            and_(Message.sender_id == other_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at.asc()).all()

    # Sidebar conversations (same as inbox)
    sent_to = db.session.query(Message.receiver_id).filter_by(sender_id=current_user.id)
    received_from = db.session.query(Message.sender_id).filter_by(receiver_id=current_user.id)
    contact_ids = set(
        [r[0] for r in sent_to.all()] +
        [r[0] for r in received_from.all()]
    )
    # Always include the current conversation partner
    contact_ids.add(other_id)

    conversations = []
    for uid in contact_ids:
        u = User.query.get(uid)
        if not u:
            continue
        last_msg = Message.query.filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == uid),
                and_(Message.sender_id == uid, Message.receiver_id == current_user.id)
            )
        ).order_by(Message.created_at.desc()).first()

        unread_count = Message.query.filter_by(
            sender_id=uid, receiver_id=current_user.id, is_read=False
        ).count()

        conversations.append({
            "user": u,
            "display_name": get_display_name(u),
            "company": get_company_name(u),
            "last_message": last_msg,
            "unread_count": unread_count,
        })

    conversations.sort(
        key=lambda c: c["last_message"].created_at if c["last_message"] else datetime.min,
        reverse=True
    )

    total_unread = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()

    is_following = Follow.query.filter_by(
        follower_id=current_user.id, followed_id=other_id
    ).first() is not None

    return render_template(
        "chat/inbox.html",
        conversations=conversations,
        active_user=other,
        active_display_name=get_display_name(other),
        active_company=get_company_name(other),
        messages=messages,
        total_unread=total_unread,
        is_following=is_following,
    )


# =========================
# SEND MESSAGE  (AJAX POST)
# =========================
@chat_bp.route("/send/<int:receiver_id>", methods=["POST"])
@login_required
def send_message(receiver_id):
    receiver = User.query.get_or_404(receiver_id)
    body = request.json.get("body", "").strip()

    if not body:
        return jsonify({"error": "Empty message"}), 400

    if len(body) > 2000:
        return jsonify({"error": "Message too long"}), 400

    msg = Message(
        sender_id=current_user.id,
        receiver_id=receiver.id,
        body=body
    )
    db.session.add(msg)
    db.session.commit()

    return jsonify({
        "id": msg.id,
        "body": msg.body,
        "sender_id": msg.sender_id,
        "created_at": msg.created_at.strftime("%b %d, %Y %I:%M %p"),
        "is_mine": True
    })


# =========================
# POLL FOR NEW MESSAGES  (AJAX GET)
# Lightweight polling — checks for messages newer than a given message id
# =========================
@chat_bp.route("/poll/<int:other_id>")
@login_required
def poll_messages(other_id):
    since_id = request.args.get("since", 0, type=int)

    new_messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == other_id),
            and_(Message.sender_id == other_id, Message.receiver_id == current_user.id)
        ),
        Message.id > since_id
    ).order_by(Message.created_at.asc()).all()

    # Mark incoming as read
    for m in new_messages:
        if m.receiver_id == current_user.id and not m.is_read:
            m.is_read = True
    db.session.commit()

    return jsonify([
        {
            "id": m.id,
            "body": m.body,
            "sender_id": m.sender_id,
            "created_at": m.created_at.strftime("%b %d, %Y %I:%M %p"),
            "is_mine": m.sender_id == current_user.id
        }
        for m in new_messages
    ])


# =========================
# UNREAD COUNT  (AJAX — for nav badge)
# =========================
@chat_bp.route("/unread-count")
@login_required
def unread_count():
    count = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    return jsonify({"count": count})
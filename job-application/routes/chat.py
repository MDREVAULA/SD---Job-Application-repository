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


def serialize_message(m, current_user_id, active_display_name=None):
    """
    Serialize a Message object to a dict for JSON responses.
    Includes reply_to fields needed by the JS appendBubble() function.
    """
    reply_to_body   = None
    reply_to_author = None

    if m.reply_to_id and m.reply_to:
        reply_to_body = m.reply_to.body
        # Determine author label: "You" if the quoted message was sent by current user
        if m.reply_to.sender_id == current_user_id:
            reply_to_author = "You"
        else:
            reply_to_author = active_display_name or "Them"

    return {
        "id":              m.id,
        "body":            m.body,
        "sender_id":       m.sender_id,
        "created_at":      m.created_at.strftime("%I:%M %p"),
        "is_mine":         m.sender_id == current_user_id,
        "edited":          m.edited,
        "reply_to_id":     m.reply_to_id,
        "reply_to_body":   reply_to_body,
        "reply_to_author": reply_to_author,
    }


# =========================
# PEOPLE PAGE
# =========================
@chat_bp.route("/people")
def people():
    query       = request.args.get("q", "").strip()
    role_filter = request.args.get("role", "").strip()

    users_query = User.query.filter(User.role != "admin")

    if current_user.is_authenticated:
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

    users_query = users_query.filter(
        or_(
            User.verification_status == "Approved",
            User.role == "applicant",
            User.role == "hr"
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
        new_follow = Follow(follower_id=current_user.id, followed_id=target.id)
        db.session.add(new_follow)
        db.session.commit()
        action = "followed"

    follower_count = Follow.query.filter_by(followed_id=target.id).count()
    return jsonify({"action": action, "follower_count": follower_count})


# =========================
# INBOX — list all conversations
# =========================
@chat_bp.route("/inbox")
@login_required
def inbox():
    sent_to       = db.session.query(Message.receiver_id).filter_by(sender_id=current_user.id)
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
            "user":         user,
            "display_name": get_display_name(user),
            "company":      get_company_name(user),
            "last_message": last_msg,
            "unread_count": unread_count,
        })

    conversations.sort(
        key=lambda c: c["last_message"].created_at if c["last_message"] else datetime.min,
        reverse=True
    )

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

    # Mark incoming messages as read
    Message.query.filter_by(
        sender_id=other_id,
        receiver_id=current_user.id,
        is_read=False
    ).update({"is_read": True})
    db.session.commit()

    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == other_id),
            and_(Message.sender_id == other_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at.asc()).all()

    # Build sidebar conversation list
    sent_to       = db.session.query(Message.receiver_id).filter_by(sender_id=current_user.id)
    received_from = db.session.query(Message.sender_id).filter_by(receiver_id=current_user.id)
    contact_ids   = set(
        [r[0] for r in sent_to.all()] +
        [r[0] for r in received_from.all()]
    )
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
            "user":         u,
            "display_name": get_display_name(u),
            "company":      get_company_name(u),
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
# Now accepts optional reply_to_id from the request body
# =========================
@chat_bp.route("/send/<int:receiver_id>", methods=["POST"])
@login_required
def send_message(receiver_id):
    receiver = User.query.get_or_404(receiver_id)
    data     = request.get_json()
    body     = (data.get("body") or "").strip()

    if not body:
        return jsonify({"error": "Empty message"}), 400

    if len(body) > 2000:
        return jsonify({"error": "Message too long"}), 400

    # ── reply support ──
    reply_to_id = data.get("reply_to_id")
    if reply_to_id:
        # Validate the quoted message actually belongs to this conversation
        quoted = Message.query.get(reply_to_id)
        if not quoted or not (
            (quoted.sender_id == current_user.id   and quoted.receiver_id == receiver_id) or
            (quoted.sender_id == receiver_id        and quoted.receiver_id == current_user.id)
        ):
            reply_to_id = None   # silently ignore invalid reply targets

    msg = Message(
        sender_id   = current_user.id,
        receiver_id = receiver.id,
        body        = body,
        reply_to_id = reply_to_id,
    )
    db.session.add(msg)
    db.session.commit()

    # Build reply preview fields for the JS
    reply_to_body   = None
    reply_to_author = None
    if reply_to_id and msg.reply_to:
        reply_to_body   = msg.reply_to.body
        reply_to_author = "You" if msg.reply_to.sender_id == current_user.id else get_display_name(receiver)

    return jsonify({
        "id":              msg.id,
        "body":            msg.body,
        "sender_id":       msg.sender_id,
        "created_at":      msg.created_at.strftime("%I:%M %p"),
        "is_mine":         True,
        "edited":          False,
        "reply_to_id":     msg.reply_to_id,
        "reply_to_body":   reply_to_body,
        "reply_to_author": reply_to_author,
    })


# =========================
# POLL FOR NEW MESSAGES  (AJAX GET)
# =========================
@chat_bp.route("/poll/<int:other_id>")
@login_required
def poll_messages(other_id):
    since_id = request.args.get("since", 0, type=int)

    other = User.query.get_or_404(other_id)

    new_messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == other_id),
            and_(Message.sender_id == other_id,        Message.receiver_id == current_user.id)
        ),
        Message.id > since_id
    ).order_by(Message.created_at.asc()).all()

    # Mark incoming as read
    for m in new_messages:
        if m.receiver_id == current_user.id and not m.is_read:
            m.is_read = True
    db.session.commit()

    other_display = get_display_name(other)

    return jsonify([
        serialize_message(m, current_user.id, other_display)
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


# =========================
# EDIT MESSAGE  (AJAX POST)
# URL: /chat/edit/<msg_id>   ← no extra /chat/ prefix, blueprint handles it
# =========================
@chat_bp.route("/edit/<int:msg_id>", methods=["POST"])
@login_required
def edit_message(msg_id):
    msg = Message.query.get_or_404(msg_id)

    if msg.sender_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    data     = request.get_json()
    new_body = (data.get("body") or "").strip()

    if not new_body:
        return jsonify({"error": "Empty message"}), 400

    if len(new_body) > 2000:
        return jsonify({"error": "Message too long"}), 400

    msg.body   = new_body
    msg.edited = True
    db.session.commit()

    return jsonify({
        "id":     msg.id,
        "body":   msg.body,
        "edited": True,
    })


# =========================
# UNSEND MESSAGE  (AJAX POST)
# URL: /chat/unsend/<msg_id>
# =========================
@chat_bp.route("/unsend/<int:msg_id>", methods=["POST"])
@login_required
def unsend_message(msg_id):
    msg = Message.query.get_or_404(msg_id)

    if msg.sender_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    # Clear reply_to_id on any messages that quoted this one
    # so child bubbles don't crash (reply_to becomes None gracefully)
    Message.query.filter_by(reply_to_id=msg_id).update({"reply_to_id": None})

    db.session.delete(msg)
    db.session.commit()

    return jsonify({"deleted": True, "id": msg_id})
